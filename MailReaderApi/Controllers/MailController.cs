using MailKit.Net.Imap;
using MailKit.Security;
using Microsoft.AspNetCore.Mvc;
using MailKit;
using System.Text.Json;
using MailReaderApi.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;

[ApiController]
[Route("api/mail")]
public class MailController : ControllerBase
{
    private readonly ILogger<MailController> _logger;
    private readonly IConfiguration _configuration;

    public MailController(ILogger<MailController> logger, IConfiguration configuration)
    {
        _logger = logger;
        _configuration = configuration;
    }

    [HttpPost("read")]
    public async Task<IActionResult> ReadMail([FromBody] MailRequest request)
    {
        if (request == null)
        {
            return BadRequest(new { error = "Request is null" });
        }

        if (string.IsNullOrEmpty(request.Email) || string.IsNullOrEmpty(request.ClientId) || string.IsNullOrEmpty(request.RefreshToken))
        {
            return BadRequest(new { error = "Email, ClientId and RefreshToken are required" });
        }

        try
        {
            var tokenResult = await TokenHelper.GetAccessTokenFromRefreshToken(request.RefreshToken, request.ClientId);
            if (tokenResult.ValueKind == JsonValueKind.Undefined)
            {
                return BadRequest(new { error = "Authentication failed." });
            }

            var accessToken = tokenResult.GetProperty("access_token").GetString();
            if (string.IsNullOrEmpty(accessToken))
            {
                return BadRequest(new { error = "No access token found." });
            }

            var filteredEmails = new List<object>();
            var allowedSenders = new[] { "info@info.textfree.us", "noreply@notifications.textnow.com" };

            using (var client = new ImapClient())
            {
                client.ServerCertificateValidationCallback = (s, c, h, e) => true;
                client.CheckCertificateRevocation = false;
                
                await client.ConnectAsync("outlook.office365.com", 993, SecureSocketOptions.SslOnConnect);
                var oauth2 = new SaslMechanismOAuth2(request.Email, accessToken);
                await client.AuthenticateAsync(oauth2);

                var foldersToCheck = new List<IMailFolder>();
                if (client.Inbox != null)
                {
                    foldersToCheck.Add(client.Inbox);
                }

                var junkFolder = await GetJunkFolderAsync(client);
                if (junkFolder != null)
                {
                    foldersToCheck.Add(junkFolder);
                }

                foreach (var folder in foldersToCheck)
                {
                    await folder.OpenAsync(FolderAccess.ReadOnly);
                    var uids = await folder.SearchAsync(MailKit.Search.SearchQuery.All);
                    var recentUids = uids.Reverse().Take(10).ToList();

                    foreach (var uid in recentUids)
                    {
                        try
                        {
                            var message = await folder.GetMessageAsync(uid);
                            var fromAddress = message.From.Mailboxes.FirstOrDefault()?.Address;

                            if (fromAddress != null && allowedSenders.Contains(fromAddress, StringComparer.OrdinalIgnoreCase))
                            {
                                filteredEmails.Add(new
                                {
                                    From = fromAddress,
                                    Subject = message.Subject,
                                    Date = message.Date.LocalDateTime.ToString("yyyy-MM-dd HH:mm"),
                                    Body = !string.IsNullOrEmpty(message.HtmlBody) ? message.HtmlBody : message.TextBody
                                });
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Error processing message {uid} in folder {folder.Name}: {ex.Message}");
                            continue;
                        }
                    }

                    await folder.CloseAsync();
                }

                await client.DisconnectAsync(true);
            }

            return Ok(filteredEmails);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error details: {ex.Message}");
            return StatusCode(500, new { error = "An error occurred while processing your request." });
        }
    }

    private async Task<IMailFolder?> GetJunkFolderAsync(ImapClient client)
    {
        var personal = client.PersonalNamespaces.FirstOrDefault();
        if (personal == null)
        {
            return null;
        }

        var folders = await client.GetFoldersAsync(personal);
        foreach (var folder in folders)
        {
            if (folder.Name.Equals("Junk Email", StringComparison.OrdinalIgnoreCase) ||
                folder.Name.Equals("Spam", StringComparison.OrdinalIgnoreCase) ||
                folder.Attributes.HasFlag(FolderAttributes.Junk))
            {
                return folder;
            }
        }

        return null;
    }
}
