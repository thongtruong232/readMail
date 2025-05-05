using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.Json;

public class TokenHelper
{
    public static async Task<JsonElement> GetAccessTokenFromRefreshToken(string refreshToken, string clientId)
    {
        using (var client = new HttpClient())
        {
            var tokenEndpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token";

            var parameters = new Dictionary<string, string>
            {
                { "client_id", clientId },
                { "refresh_token", refreshToken },
                { "grant_type", "refresh_token" },
                { "scope", "https://outlook.office.com/IMAP.AccessAsUser.All offline_access" }
            };

            var content = new FormUrlEncodedContent(parameters);

            try
            {
                var response = await client.PostAsync(tokenEndpoint, content);
                var responseContent = await response.Content.ReadAsStringAsync();
                
                if (!response.IsSuccessStatusCode)
                {
                    return default;
                }

                var result = JsonSerializer.Deserialize<JsonElement>(responseContent);
                if (result.TryGetProperty("access_token", out var token))
                {
                    return result;
                }

                return default;
            }
            catch (Exception ex)
            {
                if (ex.InnerException != null)
                {
                    Console.WriteLine($"Inner exception: {ex.InnerException.Message}");
                }
                throw new ApplicationException("Error retrieving access token", ex);
            }
        }
    }
}
