import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { searchFirms } from "@/api/firms";
import { queryKeys } from "@/api/queryKeys";
import type { FirmSummary } from "@/api/types";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { firmDetailPath } from "@/lib/navigation";
import { isUnauthorized, isServiceUnavailable } from "@/lib/errors";
import { useI18n } from "@/i18n";

function FirmRow({ firm }: { firm: FirmSummary }) {
  const { t } = useI18n();
  const metaRows = [
    firm.businessRegistrationNumber
      ? { label: t("firms.labels.ico"), value: firm.businessRegistrationNumber }
      : null,
    firm.code ? { label: t("firms.labels.customerCode"), value: firm.code } : null,
    firm.city ? { label: t("firms.labels.city"), value: firm.city } : null,
  ].filter((row): row is { label: string; value: string } => row !== null);

  return (
    <li>
      <Link to={firmDetailPath(firm.id)} className="list-card firm-card">
        <strong className="firm-card-name">{firm.name}</strong>
        {metaRows.length > 0 && (
          <dl className="firm-card-meta">
            {metaRows.map((row) => (
              <div key={row.label} className="firm-meta-row">
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </Link>
    </li>
  );
}

export function FirmSearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [take, setTake] = useState(20);
  const debouncedQ = useDebouncedValue(query.trim(), 300);
  const canSearch = debouncedQ.length >= 2;
  const { t, formatSearchResultCount } = useI18n();

  const searchQuery = useQuery({
    queryKey: queryKeys.firmsSearch(debouncedQ, take),
    queryFn: () => searchFirms(debouncedQ, take, 0),
    enabled: canSearch,
  });

  if (searchQuery.isError) {
    const err = searchQuery.error;
    if (isUnauthorized(err)) {
      navigate("/app/session-expired", { replace: true });
    } else if (isServiceUnavailable(err)) {
      navigate("/app/connection-error", {
        replace: true,
        state: { from: "/app/firms" },
      });
    }
  }

  const items = searchQuery.data?.items ?? [];
  const hasMore = searchQuery.data?.hasMore ?? false;

  return (
    <div className="firms-page page--compact">
      <header className="page-toolbar page-toolbar--title">
        <h1>{t("firms.searchTitle")}</h1>
        <button
          type="button"
          className="btn-secondary btn-secondary--small"
          onClick={() => void searchQuery.refetch()}
        >
          {t("common.refresh")}
        </button>
      </header>

      <label className="search-field">
        <span className="visually-hidden">{t("firms.searchAria")}</span>
        <input
          type="search"
          placeholder={t("firms.searchPlaceholder")}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setTake(20);
          }}
          autoComplete="off"
        />
        {query && (
          <button type="button" className="btn-clear" onClick={() => { setQuery(""); setTake(20); }}>
            {t("common.clear")}
          </button>
        )}
      </label>

      {!canSearch && <p className="hint">{t("firms.hintMinChars")}</p>}

      {canSearch && searchQuery.isLoading && (
        <ul className="skeleton-list" aria-hidden>
          <li className="skeleton-row" />
          <li className="skeleton-row" />
        </ul>
      )}

      {canSearch && searchQuery.isSuccess && items.length === 0 && (
        <p className="empty">{t("firms.empty")}</p>
      )}

      {canSearch && items.length > 0 && (
        <>
          <p className="result-count">{formatSearchResultCount(items.length)}</p>
          <ul className="firm-list">
            {items.map((firm) => (
              <FirmRow key={firm.id} firm={firm} />
            ))}
          </ul>
          {hasMore && (
            <button
              type="button"
              className="btn-secondary load-more"
              onClick={() => setTake((n) => n + 20)}
            >
              {t("common.loadMore")}
            </button>
          )}
        </>
      )}

      {canSearch && searchQuery.isError && !isUnauthorized(searchQuery.error) && (
        <p className="error" role="alert">
          {searchQuery.error instanceof Error
            ? searchQuery.error.message
            : t("firms.searchFailed")}
        </p>
      )}
    </div>
  );
}
