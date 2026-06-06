using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace MobileCrm.Adapter.Gen;

public interface IContactService
{
    Task<GenContactDetail?> GetDetailAsync(
        GenCredentials credentials,
        string contactId,
        string? firmId,
        CancellationToken ct = default);
}

public sealed class ContactService : IContactService
{
    private readonly IGenApiClient _gen;
    private readonly IFirmService _firms;
    private readonly GenOptions _options;
    private readonly ILogger<ContactService> _logger;

    public ContactService(
        IGenApiClient gen,
        IFirmService firms,
        IOptions<GenOptions> options,
        ILogger<ContactService> logger)
    {
        _gen = gen;
        _firms = firms;
        _options = options.Value;
        _logger = logger;
    }

    public async Task<GenContactDetail?> GetDetailAsync(
        GenCredentials credentials,
        string contactId,
        string? firmId,
        CancellationToken ct = default)
    {
        JsonElement root;
        try
        {
            var select = Uri.EscapeDataString(_options.PersonContactSelect);
            root = await _gen.GetAsync($"persons/{contactId}?select={select}", credentials, ct);
        }
        catch (GenApiException ex) when (ex.StatusCode == 404)
        {
            return null;
        }

        var person = FirmService.ParsePersonContact(root);
        if (person is null || person.Hidden || person.IsEmployee)
        {
            return null;
        }

        var address = person.Address;
        if (address is null
            || (string.IsNullOrWhiteSpace(address.Phone1) && string.IsNullOrWhiteSpace(address.Email)))
        {
            var addrId = GenJsonHelper.GetString(root, "Address_ID", "address_id");
            if (!string.IsNullOrWhiteSpace(addrId) && addrId is not "__________")
            {
                try
                {
                    var addrRoot = await _gen.GetAsync(
                        $"addresses/{addrId}?select=EMail,PhoneNumber1,PhoneNumber2,Street,City,PostCode,CountryCode,ShortAddress",
                        credentials,
                        ct);
                    address = AddressMapper.Map(addrRoot) ?? address;
                }
                catch (GenApiException ex)
                {
                    _logger.LogWarning(ex, "Failed to load address {AddressId}", addrId);
                }
            }
        }

        string? firmName = null;
        var isPrimary = false;
        GenAddress? firmResidence = null;
        GenAddress? firmElectronic = null;
        if (!string.IsNullOrWhiteSpace(firmId))
        {
            firmName = await ResolveFirmNameAsync(credentials, firmId, ct);
            isPrimary = await ResolveIsPrimaryAsync(credentials, firmId, contactId, ct);
            (firmResidence, firmElectronic) = await LoadFirmAddressesAsync(credentials, firmId, ct);
        }

        if (address is null
            || (string.IsNullOrWhiteSpace(address.Phone1)
                && string.IsNullOrWhiteSpace(address.Email)
                && string.IsNullOrWhiteSpace(address.Line1)))
        {
            address = firmResidence ?? firmElectronic ?? address;
        }
        else if (string.IsNullOrWhiteSpace(address.Phone1) || string.IsNullOrWhiteSpace(address.Email))
        {
            var fallback = firmResidence ?? firmElectronic;
            if (fallback is not null)
            {
                address = new GenAddress(
                    address.Line1 ?? fallback.Line1,
                    address.Street ?? fallback.Street,
                    address.City ?? fallback.City,
                    address.PostCode ?? fallback.PostCode,
                    address.CountryCode ?? fallback.CountryCode,
                    string.IsNullOrWhiteSpace(address.Phone1) ? fallback.Phone1 : address.Phone1,
                    address.Phone2 ?? fallback.Phone2,
                    string.IsNullOrWhiteSpace(address.Email) ? fallback.Email : address.Email,
                    address.Fax ?? fallback.Fax);
            }
        }

        return new GenContactDetail(
            person.Id,
            firmId,
            firmName,
            person.FirstName,
            person.LastName,
            person.DisplayName ?? $"{person.FirstName} {person.LastName}".Trim(),
            person.JobTitle,
            address,
            isPrimary,
            GenJsonHelper.GetString(root, "Comment", "comment", "Note", "note"));
    }

    private async Task<(GenAddress? Residence, GenAddress? Electronic)> LoadFirmAddressesAsync(
        GenCredentials credentials,
        string firmId,
        CancellationToken ct)
    {
        try
        {
            var root = await _gen.GetAsync($"firms/{firmId}", credentials, ct);
            return (
                AddressMapper.MapFromProperty(root, "residenceaddress_id", "ResidenceAddress_ID"),
                AddressMapper.MapFromProperty(root, "electronicaddress_id", "ElectronicAddress_ID"));
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to load firm addresses for {FirmId}", firmId);
            return (null, null);
        }
    }

    private async Task<string?> ResolveFirmNameAsync(
        GenCredentials credentials,
        string firmId,
        CancellationToken ct)
    {
        try
        {
            var root = await _gen.GetAsync($"firms/{firmId}?select=ID,Name", credentials, ct);
            return GenJsonHelper.GetString(root, "Name", "name");
        }
        catch (GenApiException ex)
        {
            _logger.LogWarning(ex, "Failed to resolve firm name for {FirmId}", firmId);
            return null;
        }
    }

    private async Task<bool> ResolveIsPrimaryAsync(
        GenCredentials credentials,
        string firmId,
        string contactId,
        CancellationToken ct)
    {
        try
        {
            var primaryId = await _firms.ResolvePrimaryContactIdAsync(credentials, firmId, ct);
            return primaryId == contactId;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to resolve primary flag for contact {ContactId}", contactId);
            return false;
        }
    }
}
