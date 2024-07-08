
"""

===============before============
int a[3] = {1,2,3};
int sum = 0;
#pragma omp for
for (int i = 0; i < 10; i++)
{
  sum += a[i];
}


===============after============
int a[3] = {1,2,3};
int sum = 0;
#pragma omp for reduction(+:sum)
for (int i = 0; i < 10; i++)
{
  sum += a[i];
}


Conditions:

1) Check that in for is just ne assignemmt:
  sum += a[i];
  sum = sum + a[i];

  product *= a[i];
  product = product * a[i];

  any_true = any_true || condition[i]; -> ||:any_true
  all_true = all_true && condition[i]; -> &&:all_true


2) Check that inside only if statement

array elements compared with variable and then assignmen to it:

if (array[i] < minimum) {
  minimum = array[i];
}

OR

if (array[i] > maximum) {
  maximum = array[i];
}

then replace with min:minimum or max:maximum

"""