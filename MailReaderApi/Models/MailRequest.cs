namespace MailReaderApi.Models
{
    public class MailRequest
    {
        public string? Email { get; set; }
        public string? RefreshToken { get; set; }
        public string? ClientId { get; set; }
    }
}