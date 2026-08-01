import TopNav from './TopNav';
import { useAuth } from '../context/AuthContext';

// Shared page shell for every authenticated screen: sticky TopNav + a
// centered content container sized per docs/FRONTEND_DESIGN.md §0.3
// (max 1280px wide, at least 32px of top padding below the nav).
export default function AppShell({ breadcrumb, children }) {
  const { userEmail, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <TopNav breadcrumb={breadcrumb} userEmail={userEmail} onLogout={logout} />
      <main className="mx-auto max-w-[1280px] px-6 pb-10 pt-8 sm:px-8">
        {children}
      </main>
    </div>
  );
}
