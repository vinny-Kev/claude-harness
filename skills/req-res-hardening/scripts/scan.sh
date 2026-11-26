#!/usr/bin/env bash
# Candidate scanner for request/response hardening. Prints `file:line [RULE] text`.
# These are LEADS, not findings: triage each by reading the code.
#   bash scan.sh [path]        (default: current directory)
# Secret-shaped hits print location only (never the value).
set -uo pipefail
root="${1:-.}"
[[ -d "$root" ]] || { echo "not a directory: $root" >&2; exit 2; }

include=(--include='*.js' --include='*.jsx' --include='*.ts' --include='*.tsx' --include='*.mjs' --include='*.cjs'
         --include='*.py' --include='*.rb' --include='*.php' --include='*.java' --include='*.kt' --include='*.go'
         --include='*.cs' --include='*.vue' --include='*.svelte' --include='*.html' --include='*.ejs' --include='*.erb')
exclude=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=build
         --exclude-dir=vendor --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=venv
         --exclude-dir=coverage --exclude-dir=.next --exclude='*.min.js' --exclude='*.test.*' --exclude='*.spec.*')

tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT

# scan RULE MODE REGEX   (MODE: text | loc-only | loc-only-i  = case-insensitive)
scan() {
  local rule="$1" mode="$2" re="$3" ci=""
  [[ "$mode" == *-i ]] && { ci="-i"; mode="${mode%-i}"; }
  grep -rnEI $ci "${include[@]}" "${exclude[@]}" -e "$re" "$root" 2>/dev/null | while IFS= read -r hit; do
    loc="${hit%%:*}:$(cut -d: -f2 <<<"$hit")"
    if [[ "$mode" == "loc-only" ]]; then
      echo "$loc [$rule] (value hidden)"
    else
      text="$(cut -d: -f3- <<<"$hit" | sed -E 's/^[[:space:]]+//' | cut -c1-160)"
      echo "$loc [$rule] $text"
    fi
  done >> "$tmp"
}

# ── Inbound: injection ──────────────────────────────────────────────
scan SQLI        text '\.(query|raw|execute|exec|queryRaw|executeRaw|\$queryRawUnsafe)\(.*(\+ *[A-Za-z_(]|\$\{|%[sd]|\.format\(|f["'"'"'])'
scan NOSQLI      text '\.(find|findOne|findOneAndUpdate|updateOne|updateMany|deleteOne|deleteMany|aggregate)\((req|request)\.(body|query|params)|\$where'
scan CMDI        text '(exec|execSync|spawn|spawnSync)\(.*(req\.|request\.|\+ *[A-Za-z_]|\$\{)|shell: *true|os\.system\(|subprocess\.[a-z_]+\(.*shell *= *True|Runtime\.getRuntime\(\)\.exec'
scan PATH        text '(sendFile|readFile|readFileSync|createReadStream|path\.(join|resolve)|open|send_file|send_from_directory)\(.*(req\.|request\.)'
scan XSS         text 'innerHTML|dangerouslySetInnerHTML|v-html|\|safe\b|document\.write\(|\{\{\{|mark_safe\(|html_safe|raw\('
scan SSRF        text '(fetch|axios\.[a-z]+|requests\.(get|post|put)|http\.get|urlopen|got)\(.*(req\.|request\.)'
scan REDIRECT    text 'redirect\(.*(req|request)\.(query|body|params)'
scan EVAL        text '\beval\(|new Function\(|pickle\.loads?\(|yaml\.load\(|unserialize\(|ObjectInputStream'

# ── Inbound: payload / assignment / access ──────────────────────────
scan MASSASSIGN  text '\.(create|update|insert|insertOne|updateOne|findByIdAndUpdate|findOneAndUpdate|set|assign)\(.*(req|request)\.(body|json)|\.\.\.(req|request)\.body|Object\.assign\(.*(req|request)\.body|\*\*(request\.(data|json)|data)\b|\$request->all\(\)|passthrough\(\)|allowUnknown: *true'
scan NOLIMIT     text 'express\.json\( *\)|bodyParser\.json\( *\)|express\.urlencoded\( *\)'
scan CORS        text "origin: *(true|['\"]\\*['\"])|Access-Control-Allow-Origin.*\\*|\\bcors\\( *\\)|CORS_ORIGIN_ALLOW_ALL *= *True"
scan CSRF-OFF    text 'csrf.*(false|disable|exempt)|csrf_exempt|\.csrf\(\)\.disable|WTF_CSRF_ENABLED *= *False'

# ── Outbound: leakage ───────────────────────────────────────────────
scan ERRLEAK     text '(res|response)\.(send|json|status\([0-9]+\)\.(send|json))\(.*(err|error|e)\b(\.(stack|message))?|traceback\.format_exc|printStackTrace|DEBUG *= *True|debug: *true'
scan SENSITIVE   text '(password_?hash|passwordHash|hashed_?password|password_digest|otp_?code|otpCode|reset_?token|resetToken|refresh_?token|refreshToken|api_?key|apiKey|secret_?key|private_?key)'
scan RAW-MODEL   text '(res|response)\.(send|json)\( *(user|users|account|customer|order|orders)\b|return +(user|account)\b *;?$|jsonify\( *(user|account)\b'
scan SECRET      loc-only-i '(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)["'"'"']? *[:=] *["'"'"'][^"'"'"'<>{}$ ]{8,}["'"'"']|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.'

if [[ -s "$tmp" ]]; then
  sort -t: -k1,1 -k2,2n -u "$tmp"
  echo
  echo "── Candidate counts by rule ──"
  grep -oE '\[[A-Z-]+\]' "$tmp" | sort | uniq -c | sort -rn
  echo
  echo "These are leads only. Triage each: confirm untrusted source → sink, or sensitive field → response."
else
  echo "No candidates found (this does not prove the code is safe)."
fi
