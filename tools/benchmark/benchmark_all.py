import os
import sys
import docker
import sacrebleu

from benchmark import benchmark_image


device = sys.argv[1].lower()
gpu = device == "gpu"
client = docker.from_env()
current_dir = os.path.dirname(os.path.realpath(__file__))


# Benchmark configuration
test_set = "wmt14"
langpair = "en-de"
num_cpus = 8
num_samples = 5 if gpu else 3


print("Downloading the test files...")
source_file = sacrebleu.get_source_file(test_set, langpair=langpair)
target_file = sacrebleu.get_reference_files(test_set, langpair=langpair)[0]


class Image:
    def __init__(self, rel_path, runs):
        self.runs = [env for run_device, env in runs if run_device == device]
        if self.runs:
            print("Building image %s..." % rel_path)
            self.image, _ = client.images.build(
                path=os.path.join(current_dir, rel_path), tag=rel_path
            )
        else:
            self.image = None

    def run(self):
        for env in self.runs:
            image_tag = self.image.tags[0]
            name = image_tag
            if env:
                name = "%s (%s)" % (
                    name,
                    ", ".join("%s=%s" % pair for pair in env.items()),
                )

            result = benchmark_image(
                image_tag,
                source_file,
                target_file,
                num_samples=num_samples,
                environment=env,
                num_cpus=num_cpus,
                use_gpu=gpu,
            )

            yield name, result


ct2_default_runs = [
    ("cpu", {"COMPUTE_TYPE": "float"}),
    ("cpu", {"COMPUTE_TYPE": "int16"}),
    ("cpu", {"COMPUTE_TYPE": "int8"}),
    ("gpu", {"COMPUTE_TYPE": "float"}),
    ("gpu", {"COMPUTE_TYPE": "int8"}),
    ("gpu", {"COMPUTE_TYPE": "float16"}),
    ("gpu", {"COMPUTE_TYPE": "int8_float16"}),
]

images = [
    Image(
        "opennmt_ende_wmt14/opennmt_tf",
        [
            ("cpu", {}),
            ("gpu", {}),
        ],
    ),
    Image(
        "opennmt_ende_wmt14/opennmt_py",
        [
            ("cpu", {"INT8": "0"}),
            ("cpu", {"INT8": "1"}),
            ("gpu", {}),
        ],
    ),
    Image(
        "opennmt_ende_wmt14/fastertransformer",
        [
            ("gpu", {"FP16": "0"}),
            ("gpu", {"FP16": "1"}),
        ],
    ),
    Image(
        "opennmt_ende_wmt14/ctranslate2",
        [
            *ct2_default_runs,
            ("cpu", {"COMPUTE_TYPE": "int8", "USE_VMAP": "1"}),
        ],
    ),
    Image(
        "opus_mt_ende/marian",
        [
            ("cpu", {"GEMM_TYPE": "float32"}),
            ("cpu", {"GEMM_TYPE": "intgemm16"}),
            ("cpu", {"GEMM_TYPE": "intgemm8"}),
            ("gpu", {"GEMM_TYPE": "float32"}),
            ("gpu", {"GEMM_TYPE": "float16"}),
        ],
    ),
    Image(
        "opus_mt_ende/ctranslate2",
        ct2_default_runs,
    ),
]

print("Running the benchmark...")
print("")

first = True
for image in images:
    for run_name, result in image.run():
        tokens_per_sec = result.num_tokens / result.translation_time

        if gpu:
            if first:
                print("| | Tokens per second | Max. GPU memory | Max. CPU memory | BLEU |")
                print("| --- | --- | --- | --- | --- |")
            print(
                "| %s | %.1f | %dMB | %dMB | %.2f |"
                % (
                    run_name,
                    tokens_per_sec,
                    int(result.max_gpu_mem),
                    int(result.max_cpu_mem),
                    result.bleu_score,
                )
            )
        else:
            if first:
                print("| | Tokens per second | Max. memory | BLEU |")
                print("| --- | --- | --- | --- |")
            print(
                "| %s | %.1f | %dMB | %.2f |"
                % (
                    run_name,
                    tokens_per_sec,
                    int(result.max_cpu_mem),
                    result.bleu_score,
                )
            )

        first = False
