# Assessing the use of LLVM as optimizer

## Godbolt analysis

```cpp
// Type your code here, or load an example.
void square(int& __restrict a, int& __restrict  b, int& __restrict  n, int& __restrict  c, int& __restrict  d, int& __restrict  o0, int& __restrict  o1, int& __restrict  valid, int& __restrict  state, int& __restrict  done) {
    a = n;
    b = n * 3;
    if ((n * 3) == n) {
        d = n * 4 + 3;
        c = n * 4 + 7;
        o0 = n * 4 + 3;
        o1 = n * 4 + 7;
        valid = 1;
        done = 1;
        state = 0xf;
    } else {
        c = n + 1;
        o0 = n + 1;
        o1 = 3;
        done = 1;
    }
    return;
}
```

```sh
x86-64 clang

-O3 -emit-llvm -g0
```

```llvm
define dso_local void @square(int&, int&, int&, int&, int&, int&, int&, int&, int&, int&)(ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %0, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %1, ptr noalias nocapture noundef nonnull readonly align 4 dereferenceable(4) %2, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %3, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %4, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %5, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %6, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %7, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %8, ptr noalias nocapture noundef nonnull writeonly align 4 dereferenceable(4) %9) local_unnamed_addr #0 {
  %11 = load i32, ptr %2, align 4
  store i32 %11, ptr %0, align 4
  %12 = mul nsw i32 %11, 3
  store i32 %12, ptr %1, align 4
  %13 = icmp eq i32 %12, %11
  br i1 %13, label %14, label %18

14:
  %15 = shl nsw i32 %11, 2
  %16 = or i32 %15, 3
  store i32 %16, ptr %4, align 4
  %17 = add nsw i32 %15, 7
  store i32 1, ptr %7, align 4
  store i32 15, ptr %8, align 4
  br label %20

18:
  %19 = add nsw i32 %11, 1
  br label %20

20:
  %21 = phi i32 [ %17, %14 ], [ %19, %18 ]
  %22 = phi i32 [ %16, %14 ], [ %19, %18 ]
  %23 = phi i32 [ %17, %14 ], [ 3, %18 ]
  store i32 %21, ptr %3, align 4
  store i32 %22, ptr %5, align 4
  store i32 %23, ptr %6, align 4
  store i32 1, ptr %9, align 4
  ret void
}

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: readwrite) uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
```
