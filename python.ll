{(int64,): [0m[0x00001100]>  # method.__main__.fib_abi:v1__abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A__long_long_ (int64_t arg1, int64_t arg3);
[0m ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐[0m[0m
[0m[0m[0m[0m│ [0m[0m [0m[0m0x1100                                                                                                                [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[37m; __main__::fib[abi:v1][abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A](long long)[0m                                       [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m  [36m;-- __main__::fib[abi:v1][abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A](long long):[0m                                  [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m  [31m[31m; DATA XREF from cpython::__main__::fib[abi:v1][abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A](long long) @ [31m0x1412(r)[0m [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m  [31m  ; method.cpython::__main__.fib_abi:v1__abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A__long_long_[0m                    [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m45: [31mmethod.__main__.fib_abi:v1__abi:c8tJTIcFKzyF2ILShI4CrgQElQb6HcpCSitgEU0A__long_long_[0m[0m (int64_t arg1, int64_t arg3);[0m [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [37m; [37marg [36mint64_t [33marg1 [32m@ rdi[0m                                                                                               [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [37m; [37marg [36mint64_t [33marg3 [32m@ rdx[0m                                                                                               [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[33mvxorps[36m xmm0[0m[0m,[36m[36m xmm0[0m[0m,[36m[36m xmm0[0m[0m[0m[0m   [0m                                                                                             [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg1[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mvmovups ymmword [0m[0m[[36mrdi [0m[0m+[36m[36m [33m0x20[0m[0m][36m[0m[0m,[36m[36m ymm0[0m[0m[0m[0m   [0m                                                                                  [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg3[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mmov qword [0m[0m[[36mrdi [0m[0m+[36m [33m8[0m[0m][36m[0m[0m,[36m rdx[0m[0m[0m[0m   [0m                                                                                            [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg1[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mmov qword [0m[0m[[36mrdi [0m[0m+[36m[36m [36m0x40[0m[0m][36m[0m[0m,[36m [33m0[0m[0m[0m[0m   [0m                                                                                           [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg1[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mmov byte [0m[0m[[36mrdi [0m[0m+[36m[36m [33m0x18[0m[0m][36m[0m[0m,[36m [33m0[0m[0m[0m[0m   [0m                                                                                            [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg1[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mmov qword [0m[0m[[36mrdi [0m[0m+[36m[36m [33m0x10[0m[0m][36m[0m[0m,[36m [33m0[0m[0m[0m[0m   [0m                                                                                           [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [31m[37m[31m[36m; arg1[0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mmov dword[36m [0m[0m[[36mrdi[0m[0m][36m[0m[0m,[36m [33m0[0m[0m[0m[0m   [0m                                                                                                  [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[33mxor[36m eax[0m[0m,[36m eax[0m[0m[0m[0m   [0m                                                                                                        [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[36mvzeroupper[0m[0m[0m[0m   [0m                                                                                                          [0m[0m[0m[0m│[0m[0m
[0m[0m[0m[0m│ [0m[0m[31mret[0m[0m[0m[0m   [0m                                                                                                                 [0m[0m[0m[0m│[0m[0m
[0m└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘[0m[0m
}
