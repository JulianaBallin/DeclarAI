import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Chat from "./pages/Chat";
import Upload from "./pages/Upload";
import BaseConhecimento from "./pages/BaseConhecimento";
import Historico from "./pages/Historico";
import Avaliacao from "./pages/Avaliacao";
import Status from "./pages/Status";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/base" element={<BaseConhecimento />} />
          <Route path="/historico" element={<Historico />} />
          <Route path="/avaliacao" element={<Avaliacao />} />
          <Route path="/status" element={<Status />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
