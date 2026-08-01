import { Link } from 'react-router-dom';

// breadcrumb: [{ label, href? }] — last entry renders as the current page (no link)
// userEmail + onLogout: omit both to render the bar without the account area
export default function TopNav({ breadcrumb = [], userEmail, onLogout }) {
  return (
    <header className="sticky top-0 z-40 flex h-nav items-center justify-between gap-4 bg-nav px-4 text-white sm:px-6">
      <div className="flex min-w-0 items-center gap-3 sm:gap-6">
        <Link
          to="/projects"
          className="shrink-0 rounded-btn text-base font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          ExamInsight
        </Link>

        {breadcrumb.length > 0 && (
          // truncate (not wrap) so a deep breadcrumb never pushes the bar
          // wider than the viewport - the current page name always matters
          // more than earlier crumbs, so it's fine for those to clip first.
          <nav className="flex min-w-0 items-center gap-2 overflow-hidden text-sm">
            {breadcrumb.map((crumb, index) => {
              const isLast = index === breadcrumb.length - 1;
              return (
                <span key={crumb.label} className="flex min-w-0 items-center gap-2">
                  {index > 0 && <span className="shrink-0 text-white/40">/</span>}
                  {crumb.href && !isLast ? (
                    <Link
                      to={crumb.href}
                      className="hidden shrink-0 rounded-btn text-white/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 sm:inline"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span
                      className={`truncate ${isLast ? 'text-white' : 'text-white/60'}`}
                    >
                      {crumb.label}
                    </span>
                  )}
                </span>
              );
            })}
          </nav>
        )}
      </div>

      {userEmail && (
        <div className="flex shrink-0 items-center gap-2 text-sm sm:gap-4">
          <span className="hidden text-white/60 sm:inline">{userEmail}</span>
          <button
            type="button"
            onClick={onLogout}
            className="rounded-btn text-white/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          >
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
