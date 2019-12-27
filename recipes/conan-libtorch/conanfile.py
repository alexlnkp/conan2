from conans import ConanFile, CMake, tools, RunEnvironment
from conans.errors import ConanInvalidConfiguration
import os


class LibtorchConan(ConanFile):
    name = "libtorch"
    version = "1.3.1"
    url = "https://github.com/pytorch/pytorch"
    homepage = "https://github.com/forwardmeasure/conan"
    topics = ("conan", "ONNX", "neural networks")
    author = "Prashanth Nandavanam <pn@forwardmeasure.com>"
    description = (
        "Tensors and Dynamic neural networks in Python with strong GPU acceleration"
    )
    license = "Apache-2.0"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "compiler", "build_type", "arch"
    short_paths = True

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "enable_parallel_build": [True, False],
        "use_ninja_build": [True, False],
        "shared": [True, False],
        "fPIC": [True, False],
        "aten_no_test": [True, False],
        "build_binary": [True, False],
        "build_docs": [True, False],
        "build_custom_protobuf": [True, False],
        "build_python": [True, False],
        "build_caffe2_ops": [True, False],
        "build_caffe2_mobile": [True, False],
        "build_named_tensor": [True, False],
        "use_static_dispatch": [True, False],
        "build_test": [True, False],
        "use_asan": [True, False],
        "use_cuda": [True, False],
        "use_rocm": [True, False],
        "use_fbgemm": [True, False],
        "use_ffmpeg": [True, False],
        "use_gflags": [True, False],
        "use_glog": [True, False],
        "use_leveldb": [True, False],
        "use_lite_proto": [True, False],
        "use_lmdb": [True, False],
        "use_metal": [True, False],
        "use_native_arch": [True, False],
        "use_nnapi": [True, False],
        "use_nnpack": [True, False],
        "use_numpy": [True, False],
        "use_observers": [True, False],
        "use_opencl": [True, False],
        "use_opencv": [True, False],
        "use_openmp": [True, False],
        "use_prof": [True, False],
        "use_qnnpack": [True, False],
        "use_pytorch_qnnpack": [True, False],
        "use_redis": [True, False],
        "use_rocksdb": [True, False],
        "use_snpe": [True, False],
        "use_system_eigen_install": [True, False],
        "use_tensorrt": [True, False],
        "use_zmq": [True, False],
        "use_zstd": [True, False],
        "use_distributed": [True, False],
        "use_tbb": [True, False],
        "build_with_torch_libs": [True, False],
    }
    default_options = {
        "enable_parallel_build": True,
        "use_ninja_build": True,
        "shared": True,
        "fPIC": True,
        "aten_no_test": False,
        "build_binary": True,
        "build_docs": False,
        "build_custom_protobuf": False,
        "build_python": True,
        "build_caffe2_ops": True,
        "build_caffe2_mobile": True,
        "build_named_tensor": False,
        "use_static_dispatch": False,
        "build_test": False,
        "use_asan": False,
        "use_cuda": False,
        "use_rocm": False,
        "use_fbgemm": True,
        "use_ffmpeg": False,
        "use_gflags": False,
        "use_glog": False,
        "use_leveldb": False,
        "use_lite_proto": False,
        "use_lmdb": False,
        "use_metal": True,
        "use_native_arch": False,
        "use_nnapi": False,
        "use_nnpack": True,
        "use_numpy": True,
        "use_observers": False,
        "use_opencl": False,
        "use_opencv": False,
        "use_openmp": True,
        "use_prof": False,
        "use_qnnpack": True,
        "use_pytorch_qnnpack": True,
        "use_redis": False,
        "use_rocksdb": False,
        "use_snpe": False,
        "use_system_eigen_install": True,
        "use_tensorrt": False,
        "use_zmq": False,
        "use_zstd": False,
        "use_distributed": True,
        "use_tbb": False,
        "build_with_torch_libs": True,
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC
            compiler_version = int(str(self.settings.compiler.version))
            if compiler_version < 14:
                raise ConanInvalidConfiguration(
                    "Libtorch can only be built with Visual Studio 2015 or higher."
                )

    def source(self):
        # I'm sure there are better/more idiomatic ways to do this, but this will do for now
        git_clone_command = (
            "git clone {}.git {} && cd {} && "
            "git checkout v{} && git submodule update --init --recursive"
        ).format(self.url, self._source_subfolder, self._source_subfolder, self.version)
        self.run(git_clone_command)

    def build_requirements(self):
        if not self.options.build_custom_protobuf:
            self.build_requires(
                "protobuf/3.8.0@forwardmeasure/stable"
            )  # Could use the one from bincrafters
        if self.options.use_system_eigen_install:
            self.build_requires("eigen/3.3.7@conan/stable")
        if self.options.build_test:
            self.build_requires("benchmark/1.4.1@bincrafters/stable")
            self.build_requires("gflags/2.2.2@bincrafters/stable")
            self.build_requires("gtest/1.8.1@bincrafters/stable")

    def _configure_cmake(self):
        # Pach caffe2/CMakeLists.txt to correctly reference aten library
        self._patch()

        env_build = dict()
        # Not sure why the build breaks becasue of missing defs for CAFFE2_PERF_WITH_AVX, etc. so just adding these for now
        env_build["CAFFE2_PERF_WITH_AVX"] = "ON"
        env_build["CAFFE2_PERF_WITH_AVX2"] = "ON"
        env_build["CAFFE2_PERF_WITH_AVX512"] = "ON"
        with tools.environment_append(env_build):
            if self.options.use_ninja_build:
                cmake = CMake(self, generator="Ninja", set_cmake_flags=True)
            else:
                cmake = CMake(self, generator="Unix Makefiles", set_cmake_flags=True)
            cmake.parallel = True if self.options.enable_parallel_build else False
            cmake = CMake(self, set_cmake_flags=True)

            cmake.verbose = True

            # Not sure why the build breaks becasue of missing defs for CAFFE2_PERF_WITH_AVX, etc. so just adding these for now
            cmake.definitions["CAFFE2_PERF_WITH_AVX"] = "ON"
            cmake.definitions["CAFFE2_PERF_WITH_AVX2"] = "ON"
            cmake.definitions["CAFFE2_PERF_WITH_AVX512"] = "ON"

            cmake.definitions["BUILD_SHARED_LIBS"] = (
                "ON" if self.options.shared else "OFF"
            )
            cmake.definitions["ATEN_NO_TEST"] = (
                "ON" if self.options.aten_no_test else "OFF"
            )
            cmake.definitions["BUILD_BINARY"] = (
                "ON" if self.options.build_binary else "OFF"
            )
            cmake.definitions["BUILD_DOCS"] = "ON" if self.options.build_docs else "OFF"
            cmake.definitions["BUILDING_WITH_TORCH_LIBS"] = (
                "ON" if self.options.build_with_torch_libs else "OFF"
            )
            cmake.definitions["BUILD_CUSTOM_PROTOBUF"] = (
                "ON" if self.options.build_custom_protobuf else "OFF"
            )
            cmake.definitions["BUILD_PYTHON"] = (
                "ON" if self.options.build_python else "OFF"
            )
            cmake.definitions["BUILD_CAFFE2_OPS"] = (
                "ON" if self.options.build_caffe2_ops else "OFF"
            )
            cmake.definitions["BUILD_CAFFE2_MOBILE"] = (
                "ON" if self.options.build_caffe2_mobile else "OFF"
            )
            cmake.definitions["BUILD_NAMEDTENSOR"] = (
                "ON" if self.options.build_named_tensor else "OFF"
            )
            cmake.definitions["BUILD_TEST"] = "ON" if self.options.build_test else "OFF"
            cmake.definitions["USE_ASAN"] = "ON" if self.options.use_asan else "OFF"
            cmake.definitions["USE_CUDA"] = "ON" if self.options.use_cuda else "OFF"
            cmake.definitions["USE_ROCM"] = "ON" if self.options.use_rocm else "OFF"
            cmake.definitions["USE_FBGEMM"] = "ON" if self.options.use_fbgemm else "OFF"
            cmake.definitions["USE_GFLAGS"] = "ON" if self.options.use_gflags else "OFF"
            cmake.definitions["USE_GLOG"] = "ON" if self.options.use_glog else "OFF"
            cmake.definitions["USE_LEVELDB"] = (
                "ON" if self.options.use_leveldb else "OFF"
            )
            cmake.definitions["USE_LITE_PROTO"] = (
                "ON" if self.options.use_lite_proto else "OFF"
            )
            cmake.definitions["USE_LMDB"] = "ON" if self.options.use_lmdb else "OFF"
            cmake.definitions["USE_METAL"] = "ON" if self.options.use_metal else "OFF"
            cmake.definitions["USE_NATIVE_ARCH"] = (
                "ON" if self.options.use_native_arch else "OFF"
            )
            cmake.definitions["USE_NNAPI"] = "ON" if self.options.use_nnapi else "OFF"
            cmake.definitions["USE_NNPACK"] = "ON" if self.options.use_nnpack else "OFF"
            cmake.definitions["USE_NUMPY"] = "ON" if self.options.use_numpy else "OFF"
            cmake.definitions["USE_OBSERVERS"] = (
                "ON" if self.options.use_observers else "OFF"
            )
            cmake.definitions["USE_OPENCL"] = "ON" if self.options.use_opencl else "OFF"
            cmake.definitions["USE_OPENCV"] = "ON" if self.options.use_opencv else "OFF"
            cmake.definitions["USE_OPENMP"] = "ON" if self.options.use_openmp else "OFF"
            cmake.definitions["USE_PROF"] = "ON" if self.options.use_prof else "OFF"
            cmake.definitions["USE_QNNPACK"] = (
                "ON" if self.options.use_qnnpack else "OFF"
            )
            cmake.definitions["USE_PYTORCH_QNNPACK"] = (
                "ON" if self.options.use_pytorch_qnnpack else "OFF"
            )
            cmake.definitions["USE_REDIS"] = "ON" if self.options.use_redis else "OFF"
            cmake.definitions["USE_ROCKSDB"] = (
                "ON" if self.options.use_rocksdb else "OFF"
            )
            cmake.definitions["USE_SNPE"] = "ON" if self.options.use_snpe else "OFF"
            cmake.definitions["USE_SYSTEM_EIGEN_INSTALL"] = (
                "ON" if self.options.use_system_eigen_install else "OFF"
            )
            cmake.definitions["USE_TENSORRT"] = (
                "ON" if self.options.use_tensorrt else "OFF"
            )
            cmake.definitions["USE_ZMQ"] = "ON" if self.options.use_zmq else "OFF"
            cmake.definitions["USE_ZSTD"] = "ON" if self.options.use_zstd else "OFF"
            cmake.definitions["USE_DISTRIBUTED"] = (
                "ON" if self.options.use_distributed else "OFF"
            )
            cmake.definitions["USE_TBB"] = "ON" if self.options.use_tbb else "OFF"

            cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def _patch(self):
        cmake_file_to_clean = os.path.join(
            self.source_folder, "source_subfolder", "caffe2", "CMakeLists.txt"
        )
        tools.replace_in_file(
            cmake_file_to_clean,
            "--yaml_dir=${CMAKE_CURRENT_BINARY_DIR}/../aten/src/ATen",
            "--yaml_dir=${CMAKE_CURRENT_BINARY_DIR}/../../aten/src/ATen",
        )

    def _build_cmake(self):
        cmake = self._configure_cmake()
        cmake.build()

    def build(self):
        if self.settings.compiler == "Visual Studio":
            with tools.vcvars(self.settings, force=True, filter_known_paths=False):
                self._build_cmake()
        else:
            self._build_cmake()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        self.copy("*.pdb", dst="lib", src=self._build_subfolder, keep_path=False)

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.cpp_info.libs.extend(tools.collect_libs(self))
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]