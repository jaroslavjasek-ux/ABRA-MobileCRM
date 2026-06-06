import { Link } from "react-router-dom";
import type { ContactSummary } from "@/api/types";
import { ChannelDisplay } from "@/features/firms/ChannelDisplay";
import { collectReachChannels } from "@/features/firms/format";
import { contactDetailPath } from "@/lib/navigation";
import { useI18n } from "@/i18n";

export function ContactCard({
  contact,
  firmId,
}: {
  contact: ContactSummary;
  firmId: string;
}) {
  const { t } = useI18n();
  const channels = collectReachChannels(
    contact.phone1 || contact.email
      ? { phone1: contact.phone1, email: contact.email }
      : undefined,
  );

  return (
    <li
      className={`contact-card-wrap${contact.isPrimary ? " contact-card-wrap--primary" : ""}`}
    >
      <div className="list-card contact-card">
        <Link to={contactDetailPath(contact.id, firmId)} className="contact-card-link">
          <div className="contact-card-head">
            <div className="contact-card-title">
              <strong>{contact.displayName}</strong>
              {contact.isPrimary && (
                <span className="badge badge-primary">{t("contact.mainContact")}</span>
              )}
            </div>
            <span className="contact-card-chevron" aria-hidden>
              ›
            </span>
          </div>
          {contact.jobTitle && <p className="contact-card-role">{contact.jobTitle}</p>}
        </Link>
        <ChannelDisplay
          phones={channels.phones}
          emails={channels.emails}
          compact
          showWebsite={false}
        />
      </div>
    </li>
  );
}
