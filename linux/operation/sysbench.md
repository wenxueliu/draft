
sysbench --test=cpu --cpu-max-prime=10000 run
sysbench --test=threads --num-threads=64 --thread-yields=2000 --thread-locks=2 run
