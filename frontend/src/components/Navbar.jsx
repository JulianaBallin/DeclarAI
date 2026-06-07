import { Link, useLocation } from "react-router-dom";
import { MessageSquare, Upload, BookOpen, History, BarChart2, TestTube } from "lucide-react";
import logo from "../assets/logo.png";

const abas = [
  { path: "/chat",      label: "Chat",                icon: MessageSquare },
  { path: "/upload",    label: "Upload",              icon: Upload },
  { path: "/base",      label: "Base de Conhecimento", icon: BookOpen },
  { path: "/historico", label: "Histórico",            icon: History },
  { path: "/avaliacao", label: "Avaliação",             icon: TestTube },
  { path: "/status",    label: "Status",               icon: BarChart2 },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <img src={logo} alt="DeclarAI" className="navbar-logo-img" />
        <span className="navbar-logo-text">DeclarAI</span>
        <span className="navbar-logo-badge">IRPF</span>
      </div>
      <div className="navbar-tabs">
        {abas.map(({ path, label, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={`navbar-tab${pathname === path ? " active" : ""}`}
          >
            <Icon size={16} />
            <span>{label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
