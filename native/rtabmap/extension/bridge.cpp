#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <csignal>
#include <climits>
#include <cstdio>
#include <exception>
#include <string>
#include <vector>
#include <opencv2/core/version.hpp>
#include <pcl/pcl_config.h>
#include <rtabmap/core/Version.h>
#include <g2o/config.h>
#ifndef RTABMAP_G2O
#error RTAB-Map must include g2o
#endif
#ifndef G2O_HAVE_CSPARSE
#error g2o must include CSparse
#endif

int campervan_export_main(int, char **);
int campervan_reprocess_main(int, char **);
extern bool g_loopForever;

namespace {
using Entry = int (*)(int, char **);

struct Signals {
    struct sigaction abort, term, interrupt;
    Signals() { sigaction(SIGABRT, nullptr, &abort); sigaction(SIGTERM, nullptr, &term); sigaction(SIGINT, nullptr, &interrupt); }
    ~Signals() {
        sigaction(SIGABRT, &abort, nullptr);
        sigaction(SIGTERM, &term, nullptr);
        sigaction(SIGINT, &interrupt, nullptr);
    }
};

PyObject *run(PyObject *arg, Entry entry, bool reprocess) {
    if (!PyList_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "argv must be a list of strings");
        return nullptr;
    }
    const Py_ssize_t n = PyList_GET_SIZE(arg);
    if (n == 0 || n > INT_MAX) {
        PyErr_SetString(PyExc_ValueError, "argv must include argv[0]");
        return nullptr;
    }
    std::vector<std::string> storage;
    storage.reserve(static_cast<size_t>(n));
    for (Py_ssize_t i = 0; i < n; ++i) {
        PyObject *item = PyList_GET_ITEM(arg, i);
        if (!PyUnicode_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "argv must be a list of strings");
            return nullptr;
        }
        Py_ssize_t size;
        const char *s = PyUnicode_AsUTF8AndSize(item, &size);
        if (!s) return nullptr;
        if (std::string(s, static_cast<size_t>(size)).find('\0') != std::string::npos) {
            PyErr_SetString(PyExc_ValueError, "argv must not contain NUL");
            return nullptr;
        }
        storage.emplace_back(s, static_cast<size_t>(size));
    }
    std::vector<char *> argv;
    argv.reserve(storage.size() + 1);
    for (auto &value : storage) argv.push_back(value.data());
    argv.push_back(nullptr);
    int result = -1;
    std::exception_ptr failure;
    std::fflush(nullptr);
    PyThreadState *state = PyEval_SaveThread();
    try {
        if (reprocess) {
            Signals signals;
            result = entry(static_cast<int>(n), argv.data());
        } else {
            result = entry(static_cast<int>(n), argv.data());
        }
    } catch (...) {
        failure = std::current_exception();
    }
    std::fflush(nullptr);
    PyEval_RestoreThread(state);
    if (failure) {
        try {
            std::rethrow_exception(failure);
        } catch (const std::exception &e) {
            PyErr_SetString(PyExc_RuntimeError, e.what());
        } catch (...) {
            PyErr_SetString(PyExc_RuntimeError, "unknown native exception");
        }
        return nullptr;
    }
    // Reprocess catches signals and can return zero after its loop was stopped.
    // Preserve the worker's failure path rather than publishing partial output.
    return PyLong_FromLong(reprocess && !g_loopForever && result == 0 ? 130 : result);
}
PyObject *invoke(PyObject *arg, Entry entry, bool reprocess) {
    try {
        return run(arg, entry, reprocess);
    } catch (const std::bad_alloc &) {
        return PyErr_NoMemory();
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "unknown native exception");
    }
    return nullptr;
}
PyObject *export_call(PyObject *, PyObject *arg) { return invoke(arg, campervan_export_main, false); }
PyObject *reprocess_call(PyObject *, PyObject *arg) { return invoke(arg, campervan_reprocess_main, true); }
PyObject *info(PyObject *, PyObject *) {
    return Py_BuildValue("{s:s,s:s,s:s,s:O,s:O,s:s,s:s}",
        "rtabmap_version", RTABMAP_VERSION, "opencv_version", CV_VERSION,
        "pcl_version", PCL_VERSION_PRETTY, "g2o_available", Py_True,
        "csparse_available", Py_True, "build_id", CAMPERVAN_BUILD_ID,
        "version_text", "RTAB-Map " RTABMAP_VERSION " / OpenCV " CV_VERSION " / PCL " PCL_VERSION_PRETTY);
}
PyMethodDef methods[] = {
    {"build_info", info, METH_NOARGS, nullptr},
    {"_run_export", export_call, METH_O, nullptr},
    {"_run_reprocess", reprocess_call, METH_O, nullptr},
    {nullptr, nullptr, 0, nullptr}
};
PyModuleDef module = {PyModuleDef_HEAD_INIT, "_native", nullptr, -1, methods};
}
PyMODINIT_FUNC PyInit__native() { return PyModule_Create(&module); }
