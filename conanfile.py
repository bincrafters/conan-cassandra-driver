from conans import ConanFile, CMake, tools
import os


class CassandraConan(ConanFile):
    name = "cassandra-driver"
    version = "2.13.0"
    description = "Cassandra C++ Driver"
    topics = ("conan", "cassandra", "driver")
    url = "https://github.com/bincrafters/conan-cassandra-driver"
    homepage = "https://github.com/datastax/cpp-driver"
    license = "Apache-2.0"

    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}

    _source_subfolder = "source_subfolder"

    requires = (
        "libuv/1.34.2",
        "openssl/1.0.2u",
    )

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        self.options["libuv"].shared = self.options.shared

    def source(self):
        sha256 = "e06b623eee50d24ec04b8c7bde582dd406b731901bc0920ae581e70960c8681c"
        source_url = " https://codeload.github.com/datastax/cpp-driver"
        extracted_name = "cpp-driver-{}".format(self.version)
        full_filename = "{}.tar.gz".format(extracted_name)
        tools.get("{0}/tar.gz/{1}".format(source_url, self.version), filename=full_filename, sha256=sha256)
        os.rename(extracted_name, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['CASS_BUILD_STATIC'] = not self.options.shared
        cmake.definitions['CASS_USE_STATIC_LIBS'] = not self.options.shared
        cmake.definitions['CASS_BUILD_SHARED'] = self.options.shared
        cmake.definitions['LIBUV_ROOT_DIR'] = self.deps_cpp_info["libuv"].rootpath
        if self.settings.os == 'Windows' and self.options.shared:
            if self.settings.compiler == 'gcc':
                libuv_library = os.path.join(self.deps_cpp_info["libuv"].rootpath, "bin", "libuv.dll")
            else:
                libuv_library = os.path.join(self.deps_cpp_info["libuv"].rootpath, "lib", "libuv.dll.lib")
            cmake.definitions['LIBUV_LIBRARY'] = libuv_library
        cmake.definitions['OPENSSL_ROOT_DIR'] = self.deps_cpp_info["openssl"].rootpath
        cmake.configure()
        self._cmake = cmake

    def build(self):
        if self.settings.os == 'Windows' and self.settings.compiler == 'gcc' and self.options.shared:
            tools.replace_in_file(os.path.join(self._source_subfolder, "cmake", "modules", "CppDriver.cmake"),
                                  "if(WIN32)\n      install",
                                  "if(WIN32 AND NOT MINGW)\n      install")
            tools.replace_in_file(os.path.join(self._source_subfolder, "cmake", "modules", "CppDriver.cmake"),
                                  'elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")',
                                  'elseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")\n' +
                                  'set(CASS_LIBS ${CASS_LIBS} iphlpapi psapi wsock32 crypt32 ws2_32 userenv)')
        self._configure_cmake()
        self._cmake.build()

    def package(self):
        self.copy(pattern="LICENSE.txt", dst="license", src=self._source_subfolder)
        self._cmake.install()

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ['cassandra']
        else:
            self.cpp_info.libs = ['cassandra_static']
        if self.settings.os == "Windows":
            self.cpp_info.libs.extend(["iphlpapi", "psapi", "wsock32", "crypt32", "ws2_32", "userenv"])
            if not self.options.shared:
                self.cpp_info.defines = ["CASS_STATIC"]
        elif self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "rt"])
            if self.settings.compiler == 'clang' and self.settings.arch == 'x86':
                self.cpp_info.libs.extend(["atomic"])
