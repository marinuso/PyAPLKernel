from ipykernel.kernelapp import IPKernelApp
from .APLKernel import APLKernel
IPKernelApp.launch_instance(kernel_class=APLKernel)

