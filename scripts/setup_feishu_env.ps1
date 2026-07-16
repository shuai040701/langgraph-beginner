param(
    [bool]$UseDefaultFields = $true
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$EnvPath = Join-Path $ProjectRoot ".env"
$ExamplePath = Join-Path $ProjectRoot ".env.example"

function U {
    param([int[]]$CodePoints)
    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Read-RequiredValue {
    param(
        [string]$Label,
        [string]$CurrentValue = ""
    )

    if ($CurrentValue) {
        $inputValue = Read-Host "$Label [$CurrentValue]"
        if ([string]::IsNullOrWhiteSpace($inputValue)) {
            return $CurrentValue
        }
        return $inputValue.Trim()
    }

    while ($true) {
        $inputValue = Read-Host $Label
        if (-not [string]::IsNullOrWhiteSpace($inputValue)) {
            return $inputValue.Trim()
        }
        Write-Host "Value is required. Please try again." -ForegroundColor Yellow
    }
}

function Read-OptionalValue {
    param(
        [string]$Label,
        [string]$DefaultValue
    )

    $inputValue = Read-Host "$Label [$DefaultValue]"
    if ([string]::IsNullOrWhiteSpace($inputValue)) {
        return $DefaultValue
    }
    return $inputValue.Trim()
}

function Get-EnvValue {
    param(
        [string[]]$Lines,
        [string]$Key
    )

    foreach ($line in $Lines) {
        if ($line -match "^\s*#?\s*$([regex]::Escape($Key))=(.*)$") {
            $value = $Matches[1].Trim()
            if ($value -in @("cli_xxx", "your_feishu_app_secret", "your_bitable_app_token", "your_table_id")) {
                return ""
            }
            return $value
        }
    }
    return ""
}

function Set-EnvValue {
    param(
        [string[]]$Lines,
        [string]$Key,
        [string]$Value
    )

    $updated = New-Object System.Collections.Generic.List[string]
    $found = $false
    foreach ($line in $Lines) {
        if ($line -match "^\s*#?\s*$([regex]::Escape($Key))=") {
            $updated.Add("$Key=$Value")
            $found = $true
        } else {
            $updated.Add($line)
        }
    }

    if (-not $found) {
        $updated.Add("$Key=$Value")
    }

    return $updated.ToArray()
}

function Assert-FeishuTableId {
    param([string]$Value)

    if ($Value.Trim().ToLower().StartsWith("vew")) {
        throw "FEISHU_BITABLE_TABLE_ID looks like a view ID starting with vew. Please use the table ID, usually starting with tbl."
    }
}

if (-not (Test-Path $EnvPath)) {
    if (-not (Test-Path $ExamplePath)) {
        throw "Cannot find .env.example."
    }
    Copy-Item -Path $ExamplePath -Destination $EnvPath
    Write-Host "Created .env from .env.example." -ForegroundColor Green
}

$lines = Get-Content -Path $EnvPath -Encoding UTF8

Write-Host ""
Write-Host "Feishu Bitable setup" -ForegroundColor Cyan
Write-Host "Prepare: Feishu App ID, App Secret, Bitable app_token, and table_id."
Write-Host "Note: table_id usually starts with tbl. Do not use a view ID starting with vew."
Write-Host "Values will be written to .env. The .env file is ignored by Git."
Write-Host ""

$appId = Read-RequiredValue "FEISHU_APP_ID" (Get-EnvValue $lines "FEISHU_APP_ID")
$appSecret = Read-RequiredValue "FEISHU_APP_SECRET" (Get-EnvValue $lines "FEISHU_APP_SECRET")
$appToken = Read-RequiredValue "FEISHU_BITABLE_APP_TOKEN" (Get-EnvValue $lines "FEISHU_BITABLE_APP_TOKEN")
$tableId = Read-RequiredValue "FEISHU_BITABLE_TABLE_ID" (Get-EnvValue $lines "FEISHU_BITABLE_TABLE_ID")
Assert-FeishuTableId $tableId
$baseUrl = Read-OptionalValue "FEISHU_BASE_URL" "https://open.feishu.cn"

$lines = Set-EnvValue $lines "FEISHU_SYNC_ENABLED" "true"
$lines = Set-EnvValue $lines "FEISHU_APP_ID" $appId
$lines = Set-EnvValue $lines "FEISHU_APP_SECRET" $appSecret
$lines = Set-EnvValue $lines "FEISHU_BITABLE_APP_TOKEN" $appToken
$lines = Set-EnvValue $lines "FEISHU_BITABLE_TABLE_ID" $tableId
$lines = Set-EnvValue $lines "FEISHU_BASE_URL" $baseUrl

if ($UseDefaultFields) {
    $fieldMap = [ordered]@{
        FEISHU_FIELD_CREATED_AT = U @(0x521B, 0x5EFA, 0x65F6, 0x95F4)
        FEISHU_FIELD_CUSTOMER_NAME = U @(0x5BA2, 0x6237, 0x540D, 0x79F0)
        FEISHU_FIELD_CONTACT = U @(0x8054, 0x7CFB, 0x65B9, 0x5F0F)
        FEISHU_FIELD_INDUSTRY = U @(0x884C, 0x4E1A)
        FEISHU_FIELD_NEED = U @(0x9700, 0x6C42)
        FEISHU_FIELD_BUDGET = U @(0x9884, 0x7B97)
        FEISHU_FIELD_TIMELINE = U @(0x65F6, 0x95F4, 0x8BA1, 0x5212)
        FEISHU_FIELD_CITY = U @(0x57CE, 0x5E02)
        FEISHU_FIELD_SOURCE = U @(0x6765, 0x6E90)
        FEISHU_FIELD_GRADE = U @(0x7EBF, 0x7D22, 0x7B49, 0x7EA7)
        FEISHU_FIELD_NOTES = U @(0x5907, 0x6CE8)
    }

    foreach ($key in $fieldMap.Keys) {
        $lines = Set-EnvValue $lines $key $fieldMap[$key]
    }
}

Set-Content -Path $EnvPath -Value $lines -Encoding UTF8

Write-Host ""
Write-Host "Feishu config saved to .env. FEISHU_SYNC_ENABLED=true." -ForegroundColor Green
Write-Host "Next: run python main.py and record one lead to test sync."
Write-Host ""
