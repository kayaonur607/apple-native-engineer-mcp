/**
 * Capability modules.
 *
 * The server is a thin protocol shell around a set of tools. Grouping those
 * tools into modules lets a user install one artefact but enable only what they
 * need — a SwiftUI developer never has to hold App Store Connect credentials,
 * and a privacy-conscious user can run with no network-facing capability at all.
 *
 * Rules this file enforces:
 *   - every tool belongs to exactly one module (asserted by a test)
 *   - an unknown module id is a startup error, not a silent no-op
 *   - `core` cannot be disabled: it is the part that explains the rest
 */

export const CORE_MODULE = "core";

/** @typedef {{ id: string, label: string, description: string, tools: string[], defaultEnabled: boolean }} ModuleSpec */

/** @type {ModuleSpec[]} */
export const MODULES = [
  {
    id: CORE_MODULE,
    label: "Core",
    description: "Project inspection, the one-call audit, diff review and environment diagnostics.",
    tools: ["audit_project", "inspect_apple_project", "review_diff", "check_environment"],
    defaultEnabled: true,
  },
  {
    id: "swift-engineering",
    label: "Swift engineering",
    description: "SwiftUI lint, accessibility, Liquid Glass adoption, localisation and widgets.",
    tools: ["lint_swiftui", "audit_accessibility", "audit_liquid_glass", "check_localization", "validate_widgets"],
    defaultEnabled: true,
  },
  {
    id: "sf-symbols",
    label: "SF Symbols",
    description: "Symbol existence and OS availability against the 9,649-entry system catalogue.",
    tools: ["validate_sf_symbols"],
    defaultEnabled: true,
  },
  {
    id: "design-tokens",
    label: "Design tokens",
    description: "Compile token JSON into SwiftUI constants and asset catalogues.",
    tools: ["forge_design_tokens"],
    defaultEnabled: true,
  },
  {
    id: "privacy-security-audit",
    label: "Privacy audit",
    description: "Required-Reason APIs and PrivacyInfo.xcprivacy validation.",
    tools: ["audit_privacy_manifest"],
    defaultEnabled: true,
  },
  {
    id: "apple-docs-research",
    label: "Apple documentation",
    description: "Live research against developer.apple.com: search, read, availability and HIG pages.",
    tools: [
      "search_apple_documentation",
      "read_apple_documentation",
      "inspect_apple_api_availability",
      "find_apple_guidelines",
    ],
    defaultEnabled: true,
  },
  {
    id: "app-store-review",
    label: "App Store review",
    description: "Listing metadata limits and URL validation.",
    tools: ["validate_app_metadata", "audit_app_store_review"],
    defaultEnabled: true,
  },
  {
    id: "aso-engine",
    label: "App Store optimization",
    description: "Budgets, keyword coverage and risky claims in listing copy. No invented market data.",
    tools: ["analyze_app_store_optimization"],
    defaultEnabled: true,
  },
  {
    id: "app-store-assets",
    label: "App Store assets",
    description: "Icon and screenshot validation.",
    tools: ["validate_app_icon", "prepare_icon_assets", "verify_icon_set", "compose_marketing_screenshots"],
    defaultEnabled: true,
  },
  {
    id: "release-readiness",
    label: "Release readiness",
    description: "The weighted gate that can return BLOCKED instead of a compliment.",
    tools: ["generate_release_report"],
    defaultEnabled: true,
  },
  {
    id: "app-store-connect",
    label: "App Store Connect",
    description: "Read-only account inspection. Requires ASC credentials; off unless enabled.",
    tools: ["app_store_connect"],
    defaultEnabled: true,
  },
];

/** @returns {ModuleSpec | undefined} */
export function moduleFor(toolName) {
  return MODULES.find((module) => module.tools.includes(toolName));
}

/** Every module id, for error messages and documentation. */
export function moduleIds() {
  return MODULES.map((module) => module.id);
}

/**
 * Resolve the enabled module set.
 *
 * `APPLE_NATIVE_MODULES` accepts a comma-separated list, or `all` (the default
 * when unset). `core` is always included.
 *
 * @param {Record<string, string | undefined>} [env]
 * @returns {{ enabled: string[], disabled: string[], source: string }}
 */
export function resolveModules(env = process.env) {
  const raw = (env.APPLE_NATIVE_MODULES ?? "").trim();

  if (raw === "" || raw.toLowerCase() === "all") {
    return {
      enabled: MODULES.filter((module) => module.defaultEnabled).map((module) => module.id),
      disabled: MODULES.filter((module) => !module.defaultEnabled).map((module) => module.id),
      source: raw === "" ? "default" : "APPLE_NATIVE_MODULES=all",
    };
  }

  const requested = raw
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);

  const unknown = requested.filter((id) => !moduleIds().includes(id));
  if (unknown.length > 0) {
    throw new Error(
      `Unknown module(s): ${unknown.join(", ")}. Valid ids: ${moduleIds().join(", ")}`,
    );
  }

  const enabled = new Set([CORE_MODULE, ...requested]);
  return {
    enabled: MODULES.filter((module) => enabled.has(module.id)).map((module) => module.id),
    disabled: MODULES.filter((module) => !enabled.has(module.id)).map((module) => module.id),
    source: "APPLE_NATIVE_MODULES",
  };
}

/** Tools exposed for a resolved module set. */
export function toolsFor(enabledIds) {
  const enabled = new Set(enabledIds);
  return MODULES.filter((module) => enabled.has(module.id)).flatMap((module) => module.tools);
}
