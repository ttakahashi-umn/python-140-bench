# 🔥 Python 3.13 vs 3.14 Performance Benchmark Suite

## 概要

このリポジトリは、**Python 3.13** と **Python 3.14** の性能差を定量的に測定・可視化するための
ベンチマークスクリプトです。

主な目的は以下の通り：

- Python 3.14 における **実行速度最適化・遅延アノテーション・サブインタープリタ** の改善効果を検証
- 各処理カテゴリ（CPU、アノテーション、スレッド、プロセス）ごとの実性能差を数値化
- JSON / CSV / グラフ による可視化と比較分析
- 将来的に **Streamlit ダッシュボード化** が可能な構成

---

## 🧩 機能一覧

| カテゴリ | 内容 | 主な狙い |
|-----------|-------|----------|
| `cpu_bound` | 数値演算ループ負荷 | Python VM の純粋性能改善確認 |
| `annotation_heavy` | アノテーション定義の大量処理 | 3.14 の遅延評価 (Deferred Annotations) 効果測定 |
| `multithread` | スレッド並列CPU処理 | GIL影響・free-threaded モード検証 |
| `multiproc` | マルチプロセス比較 | 並列性能のベースライン |
| `subinterpreter` | サブインタープリタ呼出 | Python 3.14 新機能の性能評価 |

また、各テストで以下の追加データも記録します：

- 実行時間平均・中央値・標準偏差
- メモリ使用量（psutil利用）
- GC発生回数

---

## 📦 必要なライブラリ

### 最低限必要

```bash
uv add psutil matplotlib
```

### 推奨（拡張機能付き）

```bash
uv add psutil matplotlib tqdm pandas
```

## 🚀 実行手順

### Pythonバージョンの切り替え方法

次の二つのファイルのバージョンを変更します。

- .python-version

.venvの中身を作り直します。

```bash
uv sync
```

### Python 3.13環境でベンチマーク実行

```bash
uv run python main.py
```

出力例：

```yaml
✅ JSON saved: results_py3.13_20251022_123456.json
✅ CSV saved:  results_py3.13_20251022_123456.csv

### Python 3.14環境で同様に実行

```bash
uv run python main.py
```

出力例：

```yaml
✅ JSON saved: results_py3.14_20251022_125012.json
✅ CSV saved:  results_py3.14_20251022_125012.csv
```

### 比較分析

```bash
uv run python main.py --compare results_py3.13_20251022_123456.json results_py3.14_20251022_125012.json
```

出力例：

```markdown
📈 Performance Comparison
Task                 | File1(s)      | File2(s)      | Improvement %
------------------------------------------------------------
cpu_bound            | 4.1256        | 3.7121        | 10.03
annotation_heavy     | 0.1231        | 0.0874        | 28.98
multithread          | 1.2389        | 0.9910        | 19.99
multiproc            | 1.0983        | 1.0652        | 3.01
subinterpreter       | N/A           | 0.8541        | -
```

さらに、matplotlib がインストールされていれば グラフで改善率が可視化 されます。

📊 出力ファイル構成
```pgsql
.
├── benchmark_extended.py
├── results_py3.13_20251022_123456.json
├── results_py3.14_20251022_125012.json
├── results_py3.13_20251022_123456.csv
└── results_py3.14_20251022_125012.csv
```

JSON / CSV どちらも利用可能です。
JSONは再比較・可視化用、CSVはExcelやBIツール連携用に適しています。

## ⚙️ オプション

|オプション|説明|
|---|---|
|--compare file1 file2|2つの結果JSONを比較し、改善率を出力|

## 🧠 技術ポイント

Python 3.14 の free-threaded (GILなし) モードを有効にしている場合、multithread 項目で顕著な改善が期待されます。
subinterpreter_task() は 3.14 で正式サポートされた concurrent.interpreters を利用します。
psutil によるメモリ測定はシンプルなRSS差分です（詳細分析には tracemalloc 推奨）。
gc.get_count() により、各実行後のGC統計を収集します。

## 🧮 比較の読み方

|改善率 (%)|評価|解釈|
|---|---|---|
|0〜5%|誤差範囲|ほぼ同等性能|
|5〜15%|軽度改善|VM 最適化効果あり|
|15〜30%|明確な改善|内部オーバーヘッド削減効果|
|30%以上|大幅改善|新インタープリタ or 並列処理最適化の影響大|

## 📜 ライセンス

MIT License
