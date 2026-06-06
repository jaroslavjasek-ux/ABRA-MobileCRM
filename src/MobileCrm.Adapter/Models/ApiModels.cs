namespace MobileCrm.Adapter.Models;

public sealed class SalesRepresentativeDto
{
    public required string Id { get; init; }
    public required string LoginName { get; init; }
    public required string DisplayName { get; init; }
    public string? Email { get; init; }
    public string? EmployeeNumber { get; init; }
}

public sealed class BackendProviderDto
{
    public string Name { get; init; } = "abra-gen";
    public string? Version { get; init; }
}

public sealed class SessionResponseDto
{
    public required SalesRepresentativeDto Representative { get; init; }
    public string? ExpiresAt { get; init; }
    public string? SessionToken { get; init; }
    public IReadOnlyList<string>? Capabilities { get; init; }
    public BackendProviderDto? Provider { get; init; }
}

public sealed class LoginRequestDto
{
    public required string LoginName { get; init; }
    public required string Password { get; init; }
}

public sealed class ActivitySummaryDto
{
    public required string Id { get; init; }
    public string? DocumentNumber { get; init; }
    public required string Subject { get; init; }
    public required string Status { get; init; }
    public string? ActivityTypeId { get; init; }
    public string? ActivityTypeName { get; init; }
    public string? FirmId { get; init; }
    public string? FirmName { get; init; }
    public string? ContactId { get; init; }
    public string? ContactName { get; init; }
    public required string ScheduledStart { get; init; }
    public string? ScheduledEnd { get; init; }
    public bool IsOverdue { get; init; }
}

public sealed class MyDayResponseDto
{
    public required string Date { get; init; }
    public required SalesRepresentativeDto Representative { get; init; }
    public required IReadOnlyList<ActivitySummaryDto> Today { get; init; }
    public required IReadOnlyList<ActivitySummaryDto> Overdue { get; init; }
    public int TodayCount { get; init; }
    public int OverdueCount { get; init; }
    public object? Meta { get; init; }
}

public sealed class ApiErrorDto
{
    public required ApiErrorBodyDto Error { get; init; }
}

public sealed class ApiErrorBodyDto
{
    public required string Code { get; init; }
    public required string Message { get; init; }
    public IReadOnlyList<ApiErrorDetailDto>? Details { get; init; }
    public string? TraceId { get; init; }
}

public sealed class ApiErrorDetailDto
{
    public required string Field { get; init; }
    public required string Message { get; init; }
}

public sealed class AddressDto
{
    public string? Line1 { get; init; }
    public string? Street { get; init; }
    public string? City { get; init; }
    public string? PostCode { get; init; }
    public string? CountryCode { get; init; }
    public string? Phone1 { get; init; }
    public string? Phone2 { get; init; }
    public string? Email { get; init; }
    public string? Fax { get; init; }
}

public sealed class FirmSummaryDto
{
    public required string Id { get; init; }
    public required string Name { get; init; }
    public string? Code { get; init; }
    public string? BusinessRegistrationNumber { get; init; }
    public string? City { get; init; }
    public string? CommercialStatus { get; init; }
}

public sealed class PagedResultDto<T>
{
    public required IReadOnlyList<T> Items { get; init; }
    public int Total { get; init; }
    public bool HasMore { get; init; }
}

public sealed class ContactSummaryDto
{
    public required string Id { get; init; }
    public required string DisplayName { get; init; }
    public string? FirstName { get; init; }
    public string? LastName { get; init; }
    public string? JobTitle { get; init; }
    public bool IsPrimary { get; init; }
    public string? Phone1 { get; init; }
    public string? Email { get; init; }
}

public sealed class CommercialHealthDto
{
    public string? StatusLine { get; init; }
    public string? CommercialStatus { get; init; }
    public string? CreditIndicator { get; init; }
    public string? OverdueIndicator { get; init; }
    public string? GuidanceText { get; init; }
}

public sealed class FirmDetailResponseDto
{
    public required string Id { get; init; }
    public required string Name { get; init; }
    public string? Code { get; init; }
    public string? BusinessRegistrationNumber { get; init; }
    public string? TaxNumber { get; init; }
    public string? CommercialStatus { get; init; }
    public CommercialHealthDto? CommercialHealth { get; init; }
    public AddressDto? MainAddress { get; init; }
    public AddressDto? ElectronicAddress { get; init; }
    public string? Website { get; init; }
    public required IReadOnlyList<ContactSummaryDto> Contacts { get; init; }
    public string? PrimaryContactId { get; init; }
    public required IReadOnlyList<ActivitySummaryDto> RecentActivities { get; init; }
    public object? PipelineSnapshot { get; init; }
    public string? LastModifiedAt { get; init; }
    public object? Meta { get; init; }
}

public sealed class CompleteActivityRequestDto
{
    public required string Answer { get; init; }
    public string? Description { get; init; }
}

public sealed class AddActivityNoteRequestDto
{
    public required string Note { get; init; }
}

public sealed class ActivityDetailResponseDto
{
    public required string Id { get; init; }
    public string? DocumentNumber { get; init; }
    public required string Subject { get; init; }
    public string? Description { get; init; }
    public string? Answer { get; init; }
    public required string Status { get; init; }
    public string? ActivityTypeId { get; init; }
    public string? ActivityTypeName { get; init; }
    public required string ScheduledStart { get; init; }
    public string? ScheduledEnd { get; init; }
    public required FirmSummaryDto Firm { get; init; }
    public ContactSummaryDto? Contact { get; init; }
    public string? OwnerId { get; init; }
    public string? OwnerDisplayName { get; init; }
    public bool CanEdit { get; init; }
    public bool CanComplete { get; init; }
    public bool CanAddNote { get; init; }
    public string? LastModifiedAt { get; init; }
    public object? Meta { get; init; }
}

public sealed class ContactDetailResponseDto
{
    public required string Id { get; init; }
    public string? FirmId { get; init; }
    public string? FirmName { get; init; }
    public string? FirstName { get; init; }
    public string? LastName { get; init; }
    public required string DisplayName { get; init; }
    public string? JobTitle { get; init; }
    public AddressDto? Address { get; init; }
    public bool IsPrimary { get; init; }
    public string? Notes { get; init; }
}
