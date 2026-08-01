import { Link } from 'react-router-dom';

// breadcrumb: [{ label, href? }] — last entry renders as the current page (no link)
// userEmail + onLogout: omit both to render the bar without the account area
export default function TopNav({ breadcrumb = [], userEmail, onLogout }) {
  return (
    <header className="sticky top-0 z-40 flex h-nav items-center justify-between bg-nav px-6 text-white">
      <div className="flex items-center gap-6">
        <Link to="/projects" className="text-base font-semibold">
          ExamInsight
        </Link>

        {breadcrumb.length > 0 && (
          <nav className="flex items-center gap-2 text-sm">
            {breadcrumb.map((crumb, index) => {
              const isLast = index === breadcrumb.length - 1;
              return (
                <span key={crumb.label} className="flex items-center gap-2">
                  {index > 0 && <span className="text-white/40">/</span>}
                  {crumb.href && !isLast ? (
                    <Link to={crumb.href} className="text-white/60 hover:text-white">
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className={isLast ? 'text-white' : 'text-white/60'}>
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
        <div className="flex items-center gap-4 text-sm">
          <span className="text-white/60">{userEmail}</span>
          <button
            type="button"
            onClick={onLogout}
            className="text-white/60 hover:text-white"
          >
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
