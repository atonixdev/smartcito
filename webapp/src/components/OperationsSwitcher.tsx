import { NavLink } from "react-router-dom";

const operatorViews = [
  {
    to: "/dashboard/drone",
    label: "Drone Dashboard",
    detail: "Flight controls, telemetry, camera",
  },
  {
    to: "/dashboard/robot",
    label: "Robot Dashboard",
    detail: "Ground navigation, SLAM, patrol",
  },
  {
    to: "/dashboard/cityview",
    label: "City Map Dashboard",
    detail: "City command map, alerts, assets",
  },
] as const;

export default function OperationsSwitcher() {
  return (
    <nav className="operations-switcher" aria-label="Dashboard switcher">
      {operatorViews.map((view) => (
        <NavLink
          key={view.to}
          to={view.to}
          className={({ isActive }) => `operations-switcher-link${isActive ? " is-active" : ""}`}
        >
          <strong>{view.label}</strong>
          <span>{view.detail}</span>
        </NavLink>
      ))}
    </nav>
  );
}