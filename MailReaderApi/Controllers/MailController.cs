using MailKit.Net.Imap;
using MailKit.Security;
using Microsoft.AspNetCore.Mvc;
using MimeKit;
using MailKit;
using System.Net.Http;
using System.Text.Json;
using System.Text;
using MailReaderApi.Models;

[ApiController]
[Route("api/mail")]
public class MailController : ControllerBase
{
    [HttpPost("read")]
    public async Task<IActionResult> ReadMail([FromBody] MailRequest request)
    {
        var accessToken = await GetAccessTokenAsync(request.ClientId, request.RefreshToken);
        if (string.IsNullOrEmpty(accessToken))
            return BadRequest(new { error = "Authentication failed." });

        var filteredEmails = new List<object>();
        var allowedSenders = new[] { "info@info.textfree.us", "noreply@notifications.textnow.com" };

        using (var client = new ImapClient())
        {
            await client.ConnectAsync("outlook.office365.com", 993, SecureSocketOptions.SslOnConnect);
            var oauth2 = new SaslMechanismOAuth2(request.Email, accessToken);
            await client.AuthenticateAsync(oauth2);

            // Danh sách các thư mục cần kiểm tra: Inbox và Junk Email
            var foldersToCheck = new List<IMailFolder>
            {
                client.Inbox,
                await GetJunkFolderAsync(client) // Tự động lấy thư mục Junk
            };

            foreach (var folder in foldersToCheck)
            {
                if (folder == null) continue;

                await folder.OpenAsync(FolderAccess.ReadOnly);
                var uids = await folder.SearchAsync(MailKit.Search.SearchQuery.All);

                foreach (var uid in uids.Reverse().Take(20))
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

                await folder.CloseAsync();
            }

            await client.DisconnectAsync(true);
        }

        return Ok(filteredEmails);
    }

    private async Task<IMailFolder?> GetJunkFolderAsync(ImapClient client)
    {
        // Duyệt tất cả thư mục để tìm thư mục Junk hoặc Spam
        var personal = client.PersonalNamespaces.FirstOrDefault();
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

        return null; // Không tìm thấy
    }

    private async Task<string> GetAccessTokenAsync(string clientId, string refreshToken)
    {
        var httpClient = new HttpClient();
        var content = new FormUrlEncodedContent(new[]
        {
            new KeyValuePair<string, string>("client_id", clientId),
            new KeyValuePair<string, string>("grant_type", "refresh_token"),
            new KeyValuePair<string, string>("refresh_token", refreshToken),
            new KeyValuePair<string, string>("scope", "https://outlook.office.com/IMAP.AccessAsUser.All")
        });

        var response = await httpClient.PostAsync("https://login.microsoftonline.com/common/oauth2/v2.0/token", content);
        var json = await response.Content.ReadAsStringAsync();
        var result = JsonSerializer.Deserialize<JsonElement>(json);

        return result.TryGetProperty("access_token", out var token) ? token.GetString() : null;
    }
}
