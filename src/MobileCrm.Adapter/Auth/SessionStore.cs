using MobileCrm.Adapter.Gen;

namespace MobileCrm.Adapter.Auth;

public sealed class UserSession
{
    public required string Token { get; init; }
    public required GenCredentials Credentials { get; init; }
    public required string RepUserId { get; init; }
    public DateTimeOffset CreatedAt { get; init; } = DateTimeOffset.UtcNow;
}

public interface ISessionStore
{
    UserSession Create(GenCredentials credentials, string repUserId);
    UserSession? Get(string token);
    bool Remove(string token);
}

public sealed class InMemorySessionStore : ISessionStore
{
    private readonly Dictionary<string, UserSession> _sessions = new();
    private readonly object _lock = new();

    public UserSession Create(GenCredentials credentials, string repUserId)
    {
        var token = Guid.NewGuid().ToString("N");
        var session = new UserSession
        {
            Token = token,
            Credentials = credentials,
            RepUserId = repUserId,
        };

        lock (_lock)
        {
            _sessions[token] = session;
        }

        return session;
    }

    public UserSession? Get(string token)
    {
        lock (_lock)
        {
            return _sessions.TryGetValue(token, out var session) ? session : null;
        }
    }

    public bool Remove(string token)
    {
        lock (_lock)
        {
            return _sessions.Remove(token);
        }
    }
}
