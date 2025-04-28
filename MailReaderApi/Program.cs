var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod();
    });
});

var app = builder.Build();
app.UseCors("AllowAll");

// Cấu hình lắng nghe trên tất cả các địa chỉ IP và cổng 5000
app.Urls.Add("http://0.0.0.0:5000");

app.MapControllers();
app.Run();
