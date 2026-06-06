using MobileCrm.Adapter.Gen;
using MobileCrm.Adapter.Models;

namespace MobileCrm.Adapter.Services;

public static class ApiMapping
{
    public static SalesRepresentativeDto ToDto(RepresentativeProfile profile) => new()
    {
        Id = profile.Id,
        LoginName = profile.LoginName,
        DisplayName = profile.DisplayName,
        Email = profile.Email,
        EmployeeNumber = profile.EmployeeNumber,
    };

    public static ActivitySummaryDto ToActivitySummary(
        GenActivityRow row,
        IReadOnlyDictionary<string, string> firmNames,
        bool isOverdue)
    {
        string? firmName = null;
        if (!string.IsNullOrEmpty(row.FirmId) && firmNames.TryGetValue(row.FirmId, out var name))
        {
            firmName = name;
        }

        return new ActivitySummaryDto
        {
            Id = row.Id,
            DocumentNumber = row.DocumentNumber,
            Subject = row.Subject,
            Status = row.Status,
            ActivityTypeId = row.ActivityTypeId,
            FirmId = row.FirmId,
            FirmName = firmName,
            ScheduledStart = (row.ScheduledStart ?? DateTimeOffset.UtcNow).ToString("o"),
            ScheduledEnd = row.ScheduledEnd?.ToString("o"),
            IsOverdue = isOverdue,
        };
    }

    public static AddressDto? ToAddressDto(Gen.GenAddress? address) =>
        address is null
            ? null
            : new AddressDto
            {
                Line1 = address.Line1,
                Street = address.Street,
                City = address.City,
                PostCode = address.PostCode,
                CountryCode = address.CountryCode,
                Phone1 = address.Phone1,
                Phone2 = address.Phone2,
                Email = address.Email,
                Fax = address.Fax,
            };

    public static FirmSummaryDto ToDto(Gen.GenFirmSummary firm) => new()
    {
        Id = firm.Id,
        Name = firm.Name,
        Code = firm.Code,
        BusinessRegistrationNumber = firm.BusinessRegistrationNumber,
        City = firm.City,
        CommercialStatus = firm.CommercialStatus,
    };

    public static ContactSummaryDto ToDto(Gen.GenContactSummary contact) => new()
    {
        Id = contact.Id,
        DisplayName = contact.DisplayName,
        FirstName = contact.FirstName,
        LastName = contact.LastName,
        JobTitle = contact.JobTitle,
        IsPrimary = contact.IsPrimary,
        Phone1 = contact.Phone1,
        Email = contact.Email,
    };

    public static FirmDetailResponseDto ToDto(Gen.GenFirmDetail detail, IReadOnlyDictionary<string, string>? firmNames = null)
    {
        firmNames ??= new Dictionary<string, string> { [detail.Id] = detail.Name };
        return new FirmDetailResponseDto
        {
            Id = detail.Id,
            Name = detail.Name,
            Code = detail.Code,
            BusinessRegistrationNumber = detail.BusinessRegistrationNumber,
            TaxNumber = detail.TaxNumber,
            CommercialStatus = detail.CommercialStatus,
            CommercialHealth = null,
            MainAddress = ToAddressDto(detail.MainAddress),
            ElectronicAddress = ToAddressDto(detail.ElectronicAddress),
            Website = detail.Website,
            Contacts = detail.Contacts.Select(ToDto).ToList(),
            PrimaryContactId = detail.PrimaryContactId,
            RecentActivities = detail.RecentActivities
                .Select(a => ToActivitySummary(a, firmNames, isOverdue: false))
                .ToList(),
            PipelineSnapshot = new { openDealCount = (int?)null },
            Meta = detail.Meta,
        };
    }

    public static ActivityDetailResponseDto ToDto(Gen.GenActivityDetail detail) => new()
    {
        Id = detail.Id,
        DocumentNumber = detail.DocumentNumber,
        Subject = detail.Subject,
        Description = string.IsNullOrWhiteSpace(detail.Description) ? null : detail.Description,
        Answer = string.IsNullOrWhiteSpace(detail.Answer) ? null : detail.Answer,
        Status = detail.Status,
        ActivityTypeId = detail.ActivityTypeId,
        ActivityTypeName = detail.ActivityTypeName,
        ScheduledStart = (detail.ScheduledStart ?? DateTimeOffset.UtcNow).ToString("o"),
        ScheduledEnd = detail.ScheduledEnd?.ToString("o"),
        Firm = ToDto(detail.Firm),
        Contact = detail.Contact is null ? null : ToDto(detail.Contact),
        OwnerId = detail.OwnerId,
        OwnerDisplayName = null,
        CanEdit = detail.CanEdit,
        CanComplete = detail.CanComplete,
        Meta = new { schemaVersion = "1.0" },
    };

    public static ContactDetailResponseDto ToDto(Gen.GenContactDetail contact) => new()
    {
        Id = contact.Id,
        FirmId = contact.FirmId,
        FirmName = contact.FirmName,
        FirstName = contact.FirstName,
        LastName = contact.LastName,
        DisplayName = contact.DisplayName,
        JobTitle = contact.JobTitle,
        Address = ToAddressDto(contact.Address),
        IsPrimary = contact.IsPrimary,
        Notes = contact.Notes,
    };
}
