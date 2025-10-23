// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/providers/requesty.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
const REQUESTY_BASE_URL = "https://router.requesty.ai/v1"

type URLType = "router" | "app" | "api"

const replaceCname = (baseUrl: string, type: URLType): string => {
    if (type === "router") {
        return baseUrl
    } else {
        return baseUrl.replace("router", type).replace("v1", "")
    }
}

export const toRequestyServiceUrl = (baseUrl?: string, service: URLType = "router"): URL => {
    const url = replaceCname(baseUrl ?? REQUESTY_BASE_URL, service)

    return new URL(url)
}

export const toRequestyServiceStringUrl = (baseUrl?: string, service: URLType = "router"): string => {
    return toRequestyServiceUrl(baseUrl, service).toString()
}
