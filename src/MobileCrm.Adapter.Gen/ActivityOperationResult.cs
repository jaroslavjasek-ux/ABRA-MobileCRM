namespace MobileCrm.Adapter.Gen;

public enum ActivityOperationErrorCode
{
    NotFound,
    NotEditable,
    MissingFirm,
    GenValidationFailed,
}

public sealed record ActivityOperationResult<T>(T? Value, ActivityOperationErrorCode? Error, string? Message)
{
    public static ActivityOperationResult<T> Ok(T value) => new(value, null, null);

    public static ActivityOperationResult<T> Fail(
        ActivityOperationErrorCode error,
        string message) => new(default, error, message);
}
