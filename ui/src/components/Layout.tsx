import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { FileText, BookOpen } from "lucide-react";

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();

  const linkClass = (path: string) =>
    `text-sm transition-colors ${
      location.pathname === path
        ? "text-blue-600 font-medium"
        : "text-gray-500 hover:text-gray-800"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <FileText className="w-6 h-6 text-blue-600" />
          <Link to="/" className="text-lg font-semibold tracking-tight">
            SLA Renegotiation
          </Link>
          <nav className="ml-auto flex items-center gap-4">
            <Link to="/slas" className={linkClass("/slas")}>
              <span className="flex items-center gap-1.5">
                <BookOpen className="w-4 h-4" />
                SLAs
              </span>
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        {children}
      </main>
    </div>
  );
}
