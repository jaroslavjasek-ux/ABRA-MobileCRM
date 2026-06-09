using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public sealed class GenApiException : Exception
{
    public GenApiException(int statusCode, string? body)
        : base($"Gen API returned {statusCode}")
    {
        StatusCode = statusCode;
        Body = body;
    }

    public int StatusCode { get; }
    public string? Body { get; }
}

public interface IGenApiClient
{
    Task<JsonElement> GetAsync(string pathAndQuery, GenCredentials credentials, CancellationToken ct = default);
    Task<JsonElement> PutAsync(
        string pathAndQuery,
        GenCredentials credentials,
        object body,
        CancellationToken ct = default);
    Task<JsonElement> PostAsync(
        string pathAndQuery,
        GenCredentials credentials,
        object body,
        CancellationToken ct = default);
    Task<bool> PingAsync(GenCredentials credentials, CancellationToken ct = default);
}

public sealed class GenApiClient : IGenApiClient
{
    private readonly HttpClient _http;
    private readonly GenOptions _options;

    public GenApiClient(HttpClient http, IOptions<GenOptions> options)
    {
        _http = http;
        _options = options.Value;
    }

    public async Task<bool> PingAsync(GenCredentials credentials, CancellationToken ct = default)
    {
        try
        {
            await GetAsync("currentuser", credentials, ct);
            return true;
        }
        catch (GenApiException ex) when (ex.StatusCode is 401 or 403)
        {
            return false;
        }
    }

    public async Task<JsonElement> GetAsync(string pathAndQuery, GenCredentials credentials, CancellationToken ct = default)
    {
        var baseUrl = _options.BaseUrl.TrimEnd('/');
        var path = pathAndQuery.TrimStart('/');
        var url = $"{baseUrl}/{path}";

        using var request = new HttpRequestMessage(HttpMethod.Get, url);
        request.Headers.Authorization = CreateBasicAuth(credentials);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

        using var response = await _http.SendAsync(request, ct);
        var text = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            throw new GenApiException((int)response.StatusCode, text);
        }

        if (string.IsNullOrWhiteSpace(text))
        {
            return default;
        }

        using var doc = JsonDocument.Parse(text);
        return doc.RootElement.Clone();
    }

    public async Task<JsonElement> PutAsync(
        string pathAndQuery,
        GenCredentials credentials,
        object body,
        CancellationToken ct = default)
    {
        var baseUrl = _options.BaseUrl.TrimEnd('/');
        var path = pathAndQuery.TrimStart('/');
        var url = $"{baseUrl}/{path}";

        using var request = new HttpRequestMessage(HttpMethod.Put, url);
        request.Headers.Authorization = CreateBasicAuth(credentials);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        request.Content = new StringContent(
            JsonSerializer.Serialize(body, GenJsonHelper.Options),
            Encoding.UTF8,
            "application/json");

        using var response = await _http.SendAsync(request, ct);
        var text = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            throw new GenApiException((int)response.StatusCode, text);
        }

        if (string.IsNullOrWhiteSpace(text))
        {
            return default;
        }

        using var doc = JsonDocument.Parse(text);
        return doc.RootElement.Clone();
    }

    public async Task<JsonElement> PostAsync(
        string pathAndQuery,
        GenCredentials credentials,
        object body,
        CancellationToken ct = default)
    {
        var baseUrl = _options.BaseUrl.TrimEnd('/');
        var path = pathAndQuery.TrimStart('/');
        var url = $"{baseUrl}/{path}";

        using var request = new HttpRequestMessage(HttpMethod.Post, url);
        request.Headers.Authorization = CreateBasicAuth(credentials);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        request.Content = new StringContent(
            JsonSerializer.Serialize(body, GenJsonHelper.Options),
            Encoding.UTF8,
            "application/json");

        using var response = await _http.SendAsync(request, ct);
        var text = await response.Content.ReadAsStringAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            throw new GenApiException((int)response.StatusCode, text);
        }

        if (string.IsNullOrWhiteSpace(text))
        {
            return default;
        }

        using var doc = JsonDocument.Parse(text);
        return doc.RootElement.Clone();
    }

    private static AuthenticationHeaderValue CreateBasicAuth(GenCredentials credentials)
    {
        var raw = $"{credentials.LoginName}:{credentials.Password}";
        var bytes = Encoding.UTF8.GetBytes(raw);
        return new AuthenticationHeaderValue("Basic", Convert.ToBase64String(bytes));
    }
}
