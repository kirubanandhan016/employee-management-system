import { NavLink } from "react-router-dom";
import {
  Building2,
  CalendarClock,
  CalendarOff,
  DollarSign,
  LayoutDashboard,
  ShieldCheck,
  UserCircle2,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";

export default function Sidebar({ mobileOpen, onClose }) {
  const { isPrivileged } = useAuth();

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, visible: true },
    { to: "/employees", label: "Employees", icon: Users, visible: isPrivileged },
    { to: "/departments", label: "Departments", icon: Building2, visible: true },
    { to: "/attendance", label: "Attendance", icon: CalendarClock, visible: true },
    { to: "/leaves", label: "Leave Requests", icon: CalendarOff, visible: true },
    { to: "/salaries", label: "Salaries & Payroll", icon: DollarSign, visible: true },
    { to: "/profile", label: "My Profile", icon: UserCircle2, visible: true },
  ].filter((item) => item.visible);

  const navContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200">
      <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold tracking-tight text-slate-900">PeoplePulse</p>
            <p className="text-[11px] font-medium text-brand-600">Enterprise EMS</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 lg:hidden"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-700 shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              <Icon className="h-4.5 w-4.5 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-slate-100 p-4">
        <div className="rounded-xl bg-brand-50/70 p-3.5">
          <p className="text-xs font-semibold text-brand-900">Production HR Suite</p>
          <p className="mt-0.5 text-[11px] text-brand-700">
            Role-based access & real-time PostgreSQL analytics
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <aside className="hidden w-64 shrink-0 lg:block">{navContent}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div className="fixed inset-0 bg-slate-900/50" onClick={onClose} />
          <aside className="relative z-50 w-64 max-w-[80vw]">{navContent}</aside>
        </div>
      )}
    </>
  );
}
