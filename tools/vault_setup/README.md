# Vault Setup

自動建立符合 `specs/vault-structure-spec.md` 嘅 Obsidian Vault 目錄結構。

## 用法

```bash
# 預設路徑
python setup_vault.py

# 自訂路徑
python setup_vault.py --target ~/HiveAGI
```

## 會建立咩

```
<target>/
├── 00_Inbox/              # Raw Data 暫存
├── 01_Entries/            # LLM Wiki 生成嘅筆記
├── 02_Topics/             # MOC
│   ├── _MOC_Tourism.md
│   ├── _MOC_Industrial.md
│   └── _MOC_Legal.md
├── 03_SeedPackages/       # 輸出 Seed Package
├── 04_Templates/          # entry_template.md, schema_template.md
├── 99_Archive/            # 歸檔
├── _SCHEMA.md             # 結構說明
└── _README.md             # Vault 使用說明
```

## 下一步

1. 用 Obsidian 開啟呢個資料夾作為 Vault
2. 將硬件採集嘅 Raw Data（JSON）放入 `00_Inbox/`
3. （P1）運行 LLM Wiki Engine 生成筆記到 `01_Entries/`
4. 用 `tools/seed_generator/generate_seed.py` 產出 Seed Package 到 `03_SeedPackages/`

## 聯絡

cto@goldmanglobal.com.au
