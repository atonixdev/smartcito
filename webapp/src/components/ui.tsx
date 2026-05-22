/**
 * ============================================================================
 * File: webapp/src/components/ui.tsx
 * Purpose:
 *   Shared enterprise UI primitives for SmartCito pages and dashboards.
 * ============================================================================
 */

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function PageTitle({
  eyebrow,
  title,
  subtitle,
  breadcrumb,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  breadcrumb?: string;
}) {
  return (
    <header className="page-title-row">
      {breadcrumb && <span className="breadcrumb">{breadcrumb}</span>}
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {subtitle && <p className="lead-text">{subtitle}</p>}
    </header>
  );
}

export function SectionContainer({
  eyebrow,
  title,
  subtitle,
  children,
  className = "",
}: {
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`section-container ${className}`}>
      {(eyebrow || title || subtitle) && (
        <div className="section-heading">
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          {title && <h2>{title}</h2>}
          {subtitle && <p className="section-copy">{subtitle}</p>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Grid({
  children,
  columns = 3,
  className = "",
}: {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 12;
  className?: string;
}) {
  return (
    <div className={`ui-grid ${className}`} data-columns={columns}>
      {children}
    </div>
  );
}

export function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <article className={`ui-card ${className}`}>
      {title && <h3>{title}</h3>}
      {children}
    </article>
  );
}

export function Button({
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`btn ${className}`} {...props} />;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="ui-input" {...props} />;
}

export function IconWrapper({ children }: { children: ReactNode }) {
  return <span className="icon-wrapper">{children}</span>;
}

export function Sidebar({ children }: { children: ReactNode }) {
  return <aside className="ui-sidebar">{children}</aside>;
}

export function MapContainer({ children }: { children: ReactNode }) {
  return <div className="map-container">{children}</div>;
}

export function DeviceList({ children }: { children: ReactNode }) {
  return <div className="device-list">{children}</div>;
}

export function AlertBanner({ children }: { children: ReactNode }) {
  return <div className="alert-banner">{children}</div>;
}
