# -*- coding: utf-8 -*-

# Simple Jupyter kernel for APL, using aplpy

from aplpy import APL

from ipykernel.kernelbase import Kernel

class APLKernel(Kernel):
    implementation = 'APLKernel'
    implementation_version = '0.0.1'
    banner = 'Dyalog APL over Python'

    language_info = {
            'name': 'Dyalog APL',
            'version': '1.2.3',
            'mimetype': 'text/x-apl',
            'file_extension': '.dyalog',
    }

    apl = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apl = APL.APL()
        
        self.apl.tradfn("""
            r←⍙format obj;⎕IO;⎕ML
            ⎕IO ⎕ML←1
            
            :If 0=⎕NC'display'
                'display'⎕CY'dfns.dws'
            :EndIf
            
            r←display obj

            :If 2=⍴⍴r
                r←1↓∊⎕TC[2],¨↓r
            :EndIf
        """)

        self.runAPL = self.apl.tradfn("""
            (i r)←⍙run code;⎕IO;⎕ML
            (i r)←0 ''

            ⎕IO ⎕ML←1
            :Trap 85
                rslt←1(85⌶)code~⎕TC
                (i r)←1 (⍙format rslt)
            :EndTrap
        """)

    def do_shutdown(self, restart):
        self.apl.stop()
       
    def run_APL_code(self, code):
        lines=code.split("\n")        
        
        cur = []
        inNamespace = False
        inTradfn = False

        replies = []

        for line in lines:
            
            normline=line.strip().lower()

            if normline.startswith(":namespace"):
                # start namespace
                inNamespace = True
            elif normline.startswith(":endnamespace"):
                # end namespace and fix it
                inNamespace = False
                self.apl.fix("\n".join(cur))
                cur=[]
            elif normline.startswith("∇"):
                # tradfn start/end
                if not inTradfn: 
                    # start, remove ∇
                    inTradfn=True
                    cur.append(line[line.index('∇')+1:])
                else:
                    # end, fix it
                    inTradfn=False
                    self.apl.tradfn("\n".join(cur))
                    cur=[]
            elif inNamespace or inTradfn:
                # part of a multiline definition
                cur.append(line)
            else:
                # single-line definition
                i, r = self.runAPL(line)
                if i: replies.append(r)
                    

        if inNamespace or inTradfn:
            raise APL.APLError("unfinished multiline definition")

        return "\n".join(replies)

    def do_execute(self, code, silent, store_history=True,
            user_expressons=None, allow_stdin=False):

        if not code.strip():
            return {'status': 'ok',
                    'execution_count': self.execution_count}

        try:
            response = self.run_APL_code(code)

            if not silent:
                self.send_response(self.iopub_socket,'stream',
                    {'name':'stdout','text':response})

            return {'status': 'ok',
                    'execution_count': self.execution_count}

        except APL.APLError as e:
            err = {'execution_count': self.execution_count,
                   'ename': '',
                   'evalue': str(e),
                   'traceback': []
                   }

            self.send_response(self.iopub_socket,'stream',
                    {'name':'stderr','text':str(e)})
            self.send_response(self.iopub_socket,'error',err)
            err['status']='error'
            return err




