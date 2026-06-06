namespace MobileCrm.Adapter.Gen;

public sealed record GenFirmSummary(
    string Id,
    string Name,
    string Code,
    string? BusinessRegistrationNumber,
    string? City,
    string CommercialStatus);

public sealed record GenContactSummary(
    string Id,
    string DisplayName,
    string? FirstName,
    string? LastName,
    string? JobTitle,
    bool IsPrimary,
    string? Phone1,
    string? Email);

public sealed record GenFirmDetail(
    string Id,
    string Name,
    string Code,
    string? BusinessRegistrationNumber,
    string? TaxNumber,
    string CommercialStatus,
    GenAddress? MainAddress,
    GenAddress? ElectronicAddress,
    string? Website,
    IReadOnlyList<GenContactSummary> Contacts,
    string? PrimaryContactId,
    IReadOnlyList<GenActivityRow> RecentActivities,
    object? Meta);

public sealed record GenFirmSearchResult(
    IReadOnlyList<GenFirmSummary> Items,
    int Total,
    bool HasMore);

public sealed record GenContactDetail(
    string Id,
    string? FirmId,
    string? FirmName,
    string? FirstName,
    string? LastName,
    string DisplayName,
    string? JobTitle,
    GenAddress? Address,
    bool IsPrimary,
    string? Notes);
