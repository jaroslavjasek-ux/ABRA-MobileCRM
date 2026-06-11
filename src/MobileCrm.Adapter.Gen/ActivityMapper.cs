using System.Text.Json;

namespace MobileCrm.Adapter.Gen;

public sealed record GenActivityRow(
    string Id,
    string? DocumentNumber,
    string Subject,
    string Status,
    string? ActivityTypeId,
    string? FirmId,
    DateTimeOffset? ScheduledStart,
    DateTimeOffset? ScheduledEnd);

public sealed record GenActivityDetail(
    string Id,
    string? DocumentNumber,
    string Subject,
    string Description,
    string Answer,
    string Status,
    string? ActivityTypeId,
    string? ActivityTypeName,
    DateTimeOffset? ScheduledStart,
    DateTimeOffset? ScheduledEnd,
    GenFirmSummary Firm,
    GenContactSummary? Contact,
    string? OwnerId,
    string? OwnerDisplayName,
    bool CanEdit,
    bool CanComplete,
    bool CanAddNote);

public static class ActivityMapper
{
    // List projection: DisplayName only — Code is not accepted on DEMO list select (400).
    private const string ActivitySelect =
        "ID,DisplayName,Subject,Status,ActivityType_ID,Firm_ID,SheduledStart$DATE,SheduledEnd$DATE";

    // Detail select: no Code — DEMO returns 400 when Code is in select on GET by id.
    public const string ActivityDetailSelect =
        "ID,DisplayName,Subject,Description,Answer,Status,Firm_ID,Person_ID,ResponsibleUser_ID,"
        + "SolverUser_ID,CreatedBy_ID,ActivityType_ID,SheduledStart$DATE,SheduledEnd$DATE,ObjVersion";

    public static string ActivitySelectList => ActivitySelect;

    /// <summary>
    /// My Day ownership: activities the rep is expected to work on (solver or responsible).
    /// Does not include <c>CreatedBy_ID</c> — see Sprint 4.1.1.
    /// </summary>
    public static string BuildOwnershipWhere(string repUserId) =>
        $"(ResponsibleUser_ID eq '{repUserId}' or SolverUser_ID eq '{repUserId}')";

    public static string BuildActivitiesQuery(string repUserId, int take) =>
        $"crmactivities?select={Uri.EscapeDataString(ActivitySelect)}&where={Uri.EscapeDataString(BuildOwnershipWhere(repUserId))}&take={take}";

    public static IReadOnlyList<GenActivityRow> ParseList(JsonElement root)
    {
        var items = new List<GenActivityRow>();
        if (root.ValueKind == JsonValueKind.Array)
        {
            foreach (var el in root.EnumerateArray())
            {
                items.Add(ParseRow(el));
            }
        }
        else if (root.ValueKind == JsonValueKind.Object)
        {
            foreach (var name in new[] { "items", "value", "data" })
            {
                if (root.TryGetProperty(name, out var arr) && arr.ValueKind == JsonValueKind.Array)
                {
                    foreach (var el in arr.EnumerateArray())
                    {
                        items.Add(ParseRow(el));
                    }
                    break;
                }
            }

            // Gen may return a single row object when take=1 (not wrapped in an array).
            if (items.Count == 0 && GetCanonicalId(root) is not null)
            {
                items.Add(ParseRow(root));
            }
        }

        return items;
    }

    public static string? GetCanonicalId(JsonElement el) =>
        GenJsonHelper.GetString(el, "ID", "id");

    public static GenActivityRow ParseRow(JsonElement el)
    {
        var id = GetCanonicalId(el) ?? "";
        var subject = GenJsonHelper.GetString(el, "Subject", "subject") ?? "";
        var statusCode = GenJsonHelper.GetInt(el, "Status", "status");
        var firmId = GenJsonHelper.GetString(el, "Firm_ID", "firm_ID", "firm_id", "firmId");
        var typeId = GenJsonHelper.GetString(
            el,
            "ActivityType_ID",
            "activityType_ID",
            "activitytype_id",
            "activityTypeId");
        var start = GenJsonHelper.GetDateTime(
            el,
            "SheduledStart$DATE",
            "sheduledStart$DATE",
            "sheduledstart$date",
            "scheduledStart");
        var end = GenJsonHelper.GetDateTime(
            el,
            "SheduledEnd$DATE",
            "sheduledEnd$DATE",
            "sheduledend$date",
            "scheduledEnd");

        return new GenActivityRow(
            id,
            ResolveDocumentNumber(el, id),
            subject,
            MapStatus(statusCode),
            typeId,
            firmId,
            start,
            end);
    }

    /// <summary>ABRA document number (e.g. NP-20/2025) — DisplayName, then Code; never the technical ID.</summary>
    public static string? ResolveDocumentNumber(JsonElement el, string? canonicalId = null)
    {
        var displayName = GenJsonHelper.GetString(el, "DisplayName", "displayname");
        var code = GenJsonHelper.GetString(el, "Code", "code");

        foreach (var value in new[] { displayName, code })
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                continue;
            }

            var trimmed = value.Trim();
            if (!string.IsNullOrEmpty(canonicalId)
                && trimmed.Equals(canonicalId, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            return trimmed;
        }

        return null;
    }

    public static string MapStatus(int? status) => status switch
    {
        0 => "open",
        1 => "inProgress",
        2 => "completed",
        3 => "handedOver",
        null => "unknown",
        _ => "unknown",
    };

    public static int? GetGenStatusCode(JsonElement el) =>
        GenJsonHelper.GetInt(el, "Status", "status");

    public static bool IsGenTerminalStatus(int? statusCode) => statusCode is 2 or 3;

    public static bool IsOpenStatus(string status) =>
        status is "open" or "inProgress";

    public static bool IsTerminalStatus(string status) =>
        status is "completed" or "handedOver" or "unknown";

    public static bool CanStart(string status) => status == "open";

    public static bool CanComplete(string status) => status == "inProgress";

    public static bool CanAddNote(string status) => IsOpenStatus(status);

    public static int ToGenStatusCode(string status) => status switch
    {
        "open" => 0,
        "inProgress" => 1,
        "completed" => 2,
        "handedOver" => 3,
        _ => 0,
    };

    public static GenActivityRow ParseDetailRow(JsonElement el) => ParseRow(el);

    public static bool IsOwnedByRepresentative(JsonElement el, string repUserId)
    {
        foreach (var field in new[]
                 {
                     "ResponsibleUser_ID", "responsibleuser_id",
                     "SolverUser_ID", "solveruser_id",
                     "CreatedBy_ID", "createdby_id",
                 })
        {
            var id = GenJsonHelper.GetString(el, field);
            if (!string.IsNullOrEmpty(id) && id == repUserId)
            {
                return true;
            }
        }

        return false;
    }

    public static string? GetDescription(JsonElement el) =>
        GenJsonHelper.GetString(el, "Description", "description");

    public static string? GetAnswer(JsonElement el) =>
        GenJsonHelper.GetString(el, "Answer", "answer");

    /// <summary>
    /// Resolves Description and Answer for a follow-up activity created from a source row.
    /// Gen does not copy text fields when <c>Source_ID</c> is set — adapter must send them explicitly.
    /// </summary>
    public static (string? Description, string? Answer) ResolveFollowUpTextFields(
        string? sourceDescription,
        string? sourceAnswer,
        string? userDescription)
    {
        var description = !string.IsNullOrWhiteSpace(userDescription)
            ? userDescription.Trim()
            : string.IsNullOrWhiteSpace(sourceDescription)
                ? null
                : sourceDescription.Trim();

        var answer = string.IsNullOrWhiteSpace(sourceAnswer) ? null : sourceAnswer.Trim();

        return (description, answer);
    }

    /// <summary>
    /// Prepends a new note to existing ABRA Answer (newest first) without overwriting prior content.
    /// </summary>
    public static string AppendAnswer(
        string? existingAnswer,
        string newEntry,
        DateTimeOffset timestamp,
        string? author = null)
    {
        var trimmedNew = newEntry.Trim();
        var header = FormatAnswerHeader(timestamp, author);
        var formattedEntry = $"{header}\n{trimmedNew}";

        if (string.IsNullOrWhiteSpace(existingAnswer))
        {
            return formattedEntry;
        }

        return $"{formattedEntry}\n\n---\n\n{existingAnswer.Trim()}";
    }

    private static string FormatAnswerHeader(DateTimeOffset timestamp, string? author)
    {
        var stamp = FormatAnswerTimestamp(timestamp);
        return string.IsNullOrWhiteSpace(author) ? stamp : $"{stamp} | {author.Trim()}";
    }

    private static string FormatAnswerTimestamp(DateTimeOffset timestamp)
    {
        var timeZone = TimeZoneInfo.FindSystemTimeZoneById(
            OperatingSystem.IsWindows() ? "Central European Standard Time" : "Europe/Bratislava");
        var local = TimeZoneInfo.ConvertTime(timestamp, timeZone);
        return local.ToString("dd.MM.yyyy HH:mm");
    }

    public static string? GetPersonId(JsonElement el) =>
        GenJsonHelper.GetString(el, "Person_ID", "person_ID", "person_id", "personId");

    public static string? GetOwnerId(JsonElement el) =>
        GetResponsibleUserId(el);

    public static string? GetResponsibleUserId(JsonElement el) =>
        GenJsonHelper.GetString(el, "ResponsibleUser_ID", "responsibleuser_id", "responsibleUserId");

    public static string? GetSolverUserId(JsonElement el) =>
        GenJsonHelper.GetString(el, "SolverUser_ID", "solveruser_id", "solverUserId");

    public static string? GetBusOrderId(JsonElement el) =>
        GenJsonHelper.GetString(el, "BusOrder_ID", "busorder_id");

    public static string? GetBusProjectId(JsonElement el) =>
        GenJsonHelper.GetString(el, "BusProject_ID", "busproject_id");

    public static string? GetBusTransactionId(JsonElement el) =>
        GenJsonHelper.GetString(el, "BusTransaction_ID", "bustransaction_id");

    public sealed record GenActivityReferenceFields(
        string ActQueueId,
        string PeriodId,
        string DivisionId,
        string SolverRoleId,
        string ActivityAreaId);

    public static bool TryGetReferenceFields(JsonElement el, out GenActivityReferenceFields fields)
    {
        var actQueue = GenJsonHelper.GetString(el, "ActQueue_ID", "actqueue_id");
        var period = GenJsonHelper.GetString(el, "Period_ID", "period_id");
        var division = GenJsonHelper.GetString(el, "Division_ID", "division_id");
        var solverRole = GenJsonHelper.GetString(el, "SolverRole_ID", "solverrole_id");
        var activityArea = GenJsonHelper.GetString(el, "ActivityArea_ID", "activityarea_id");

        if (string.IsNullOrWhiteSpace(actQueue)
            || string.IsNullOrWhiteSpace(period)
            || string.IsNullOrWhiteSpace(division)
            || string.IsNullOrWhiteSpace(solverRole)
            || string.IsNullOrWhiteSpace(activityArea))
        {
            fields = default!;
            return false;
        }

        fields = new GenActivityReferenceFields(
            actQueue,
            period,
            division,
            solverRole,
            activityArea);
        return true;
    }

    public static bool IsValidPersonId(string? personId) =>
        !string.IsNullOrWhiteSpace(personId)
        && personId is not "0000000000"
        && personId is not "__________";
}
