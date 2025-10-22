# main.py
import argparse
import csv
import gc
import importlib.util
import json
import multiprocessing
import statistics
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

# 型チェッカー向けの型定義
if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import psutil
else:
    # 実行時の動的インポート
    HAS_PSUTIL = importlib.util.find_spec("psutil") is not None
    HAS_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None

    if HAS_PSUTIL:
        import psutil
    else:
        psutil = None

    if HAS_MATPLOTLIB:
        import matplotlib.pyplot as plt
    else:
        plt = None

# 実行時用の可用性フラグ（TYPE_CHECKINGブロックの外で定義）
if not TYPE_CHECKING:
    pass  # 上で既に定義済み
else:
    # 型チェック時にも可用性フラグを定義
    HAS_PSUTIL = True
    HAS_MATPLOTLIB = True

# subinterpretersは実験的機能のため無効化
interpreters = None

# subinterpretersは実験的機能のため無効化
interpreters = None

# === Utility ===


def timeit(func, *, loops=5):
    times = []
    for _ in range(loops):
        gc.collect()
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "raw": times,
    }


def measure_memory(func):
    if not HAS_PSUTIL or psutil is None:
        return None
    proc = psutil.Process()
    before = proc.memory_info().rss
    func()
    after = proc.memory_info().rss
    return (after - before) / 1024 / 1024  # MB


# === Benchmark targets ===


def cpu_bound_task(n=10_000_00):
    s = 0
    for i in range(n):
        s += (i ^ (i << 1)) % (i + 1)
    return s


def annotation_heavy_task():
    class A:
        def method(self, x: int, y: float, z: str) -> dict[str, int]:
            return {z: int(x + y)}

    def f(a: A, b: int) -> list[int]:
        return [b + i for i in range(1000)]

    a = A()
    return f(a, 5)


def _multiprocess_worker(count, q):
    """Worker function for multiprocessing. Must be defined at module level."""
    s = 0
    for i in range(count):
        s += (i * i) ^ (i >> 1)
    q.put(s)


def multithread_task(thread_count=4, work_iterations=250_000):
    def worker(count):
        s = 0
        for i in range(count):
            s += (i * i) ^ (i >> 1)
        return s

    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=worker, args=(work_iterations,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def multiproc_task(proc_count=4, work_iterations=250_000):
    q = multiprocessing.Queue()
    procs = []
    for _ in range(proc_count):
        p = multiprocessing.Process(
            target=_multiprocess_worker, args=(work_iterations, q)
        )
        procs.append(p)
        p.start()
    results = [q.get() for _ in procs]
    for p in procs:
        p.join()
    return results


# === 3.14新機能: サブインタープリタ性能チェック ===
def subinterpreter_task():
    # Python 3.14のsubinterpretersは実験的機能のため、
    # この実装では利用可能性のチェックのみ行う
    return "subinterpreter_not_implemented"


# === 実行関数 ===


def run_all():
    print(f"Running benchmarks on Python {sys.version.split()[0]}")
    results = {}
    categories = {
        "cpu_bound": cpu_bound_task,
        "annotation_heavy": annotation_heavy_task,
        "multithread": multithread_task,
        "multiproc": multiproc_task,
        "subinterpreter": subinterpreter_task,
    }

    for name, func in categories.items():
        print(f"→ Running {name}...")
        timing = timeit(func)
        mem = measure_memory(func) if HAS_PSUTIL else None
        gc_counts = gc.get_count()
        results[name] = {
            "timing": timing,
            "memory_MB": mem,
            "gc_counts": gc_counts,
        }
    return results


# === 保存・比較 ===


def save_results(results, path_prefix="results"):
    version = sys.version.split()[0]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname_json = f"{path_prefix}_py{version}_{ts}.json"
    fname_csv = f"{path_prefix}_py{version}_{ts}.csv"

    # JSON保存
    with open(fname_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"✅ JSON saved: {fname_json}")

    # CSV保存
    with open(fname_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "mean_sec", "median_sec", "stdev_sec", "memory_MB"])
        for task, data in results.items():
            t = data["timing"]
            writer.writerow(
                [
                    task,
                    round(t["mean"], 5),
                    round(t["median"], 5),
                    round(t["stdev"], 5),
                    round(data.get("memory_MB") or 0, 3),
                ]
            )
    print(f"✅ CSV saved: {fname_csv}")

    return fname_json, fname_csv


def compare_results(file1, file2):
    with open(file1, encoding="utf-8") as f1, open(file2, encoding="utf-8") as f2:
        r1, r2 = json.load(f1), json.load(f2)
    tasks = sorted(set(r1.keys()) | set(r2.keys()))
    print("\n📈 Performance Comparison")
    print(f"{'Task':<20} | {'File1(s)':<12} | {'File2(s)':<12} | {'Improvement %':<12}")
    print("-" * 60)
    ratios = {}
    for task in tasks:
        try:
            t1 = r1[task]["timing"]["mean"]
            t2 = r2[task]["timing"]["mean"]
            diff = ((t1 - t2) / t1) * 100
            ratios[task] = diff
            print(f"{task:<20} | {t1:<12.4f} | {t2:<12.4f} | {diff:<12.2f}")
        except KeyError:
            continue
    if HAS_MATPLOTLIB and plt is not None:
        plt.barh(list(ratios.keys()), list(ratios.values()))
        plt.xlabel("Improvement (%) - positive means faster in file2")
        plt.title("Python 3.13 vs 3.14 Benchmark Comparison")
        plt.tight_layout()
        plt.show()


# === CLI ===


if __name__ == "__main__":
    # macOS/Windowsでマルチプロセッシングの安全性を確保
    multiprocessing.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser(description="Python version benchmark")
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("file1", "file2"),
        help="Compare two result JSON files",
    )
    args = parser.parse_args()

    if args.compare:
        compare_results(*args.compare)
    else:
        results = run_all()
        save_results(results)
        print("✅ Benchmarking completed.")
