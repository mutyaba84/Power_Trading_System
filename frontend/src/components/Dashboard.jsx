import TerminalKpis from "./TerminalKpis.jsx";
import MarketSentiment from "./MarketSentiment.jsx";
import Card from "./Card.jsx";
import AIDecision from "./AIDecision.jsx";
import TradeTape from "./TradeTape.jsx";
import EquityCurve from "./EquityCurve.jsx";
import ControllerControls from "./ControllerControls.jsx";





export default function Dashboard() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0b0f14",
        color: "#e5e7eb",
        padding: 32,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>
        ⚡ Power Trading System
      </h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 20,
          alignItems: "start",
        }}
      >
        <TerminalKpis />
        <ControllerControls />
        <MarketSentiment />
        <AIDecision />
        <TradeTape />
        <EquityCurve />
      </div>
    </div>
  );
}
