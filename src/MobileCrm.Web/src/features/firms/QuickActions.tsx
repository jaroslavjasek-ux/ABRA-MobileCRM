import { mailHref, telHref, webHref } from "@/features/firms/format";
import { useI18n } from "@/i18n";

type QuickActionsProps = {
  phones?: string[];
  emails?: string[];
  website?: string;
  compact?: boolean;
};

export function QuickActions({ phones = [], emails = [], website, compact }: QuickActionsProps) {
  const { t } = useI18n();
  const hasActions = phones.length > 0 || emails.length > 0 || Boolean(website);
  if (!hasActions) {
    return null;
  }

  const phone = phones[0];
  const email = emails[0];

  return (
    <div className={`action-row${compact ? " action-row--compact" : ""}`}>
      {phone && (
        <a href={telHref(phone)} className="action-chip action-chip--call">
          {t("channel.call")}
        </a>
      )}
      {email && (
        <a href={mailHref(email)} className="action-chip action-chip--email">
          {t("channel.emailAction")}
        </a>
      )}
      {website && (
        <a
          href={webHref(website)}
          className="action-chip action-chip--web"
          target="_blank"
          rel="noreferrer"
        >
          {t("channel.websiteAction")}
        </a>
      )}
    </div>
  );
}
