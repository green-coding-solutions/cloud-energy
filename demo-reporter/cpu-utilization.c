#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>

typedef struct procfs_time_t { // struct is a specification and this static makes no sense here
    unsigned long user_time;
    unsigned long nice_time;
    unsigned long system_time;
    unsigned long wait_time;
    unsigned long iowait_time;
    unsigned long irq_time;
    unsigned long softirq_time;
    unsigned long steal_time;
    unsigned long guest_time;
    unsigned long compute_time; // custom attr by us not in standard /proc/stat format
    unsigned long idle_time; // custom attr by us not in standard /proc/stat format
} procfs_time_t;


// All variables are made static, because we believe that this will
// keep them local in scope to the file and not make them persist in state
// between Threads.
// TODO: If this code ever gets multi-threaded please review this assumption to
// not pollute another threads state
static long int user_hz;
static unsigned int msleep_time=1000;

static void read_cpu_proc(procfs_time_t* procfs_time_struct) {

    FILE* fd = NULL;

    fd = fopen("/proc/stat", "r");
    if ( fd == NULL) {
        fprintf(stderr, "Error - file %s failed to open: errno: %d\n", "/proc/stat/", errno);
        exit(1);
    }

    fscanf(fd, "cpu %ld %ld %ld %ld %ld %ld %ld %ld %ld", &procfs_time_struct->user_time, &procfs_time_struct->nice_time, &procfs_time_struct->system_time, &procfs_time_struct->wait_time, &procfs_time_struct->iowait_time, &procfs_time_struct->irq_time, &procfs_time_struct->softirq_time, &procfs_time_struct->steal_time, &procfs_time_struct->guest_time);

    // debug
    // printf("Read: cpu %ld %ld %ld %ld %ld %ld %ld %ld %ld\n", procfs_time_struct->user_time, procfs_time_struct->nice_time, procfs_time_struct->system_time, procfs_time_struct->idle_time, procfs_time_struct->iowait_time, procfs_time_struct->irq_time, procfs_time_struct->softirq_time, procfs_time_struct->steal_time, procfs_time_struct->guest_time);

    fclose(fd);

    // after this multiplication we are on microseconds
    // integer division is deliberately, cause we don't loose precision as *1000000 is done before

    procfs_time_struct->idle_time = procfs_time_struct->wait_time + procfs_time_struct->iowait_time + procfs_time_struct->irq_time + procfs_time_struct->softirq_time;
    // in /proc/stat nice time is NOT included in the user time! (it is in cgroups however though)
    procfs_time_struct->compute_time = procfs_time_struct->user_time + procfs_time_struct->system_time + procfs_time_struct->nice_time;

}


static int output_stats(int show_diff_time) {
    long int idle_reading, compute_time_reading;
    procfs_time_t main_cpu_reading_before;
    procfs_time_t main_cpu_reading_after;
    struct timeval start, end;

    gettimeofday(&start, NULL);
    read_cpu_proc(&main_cpu_reading_before);

    usleep(msleep_time * 1000);

    gettimeofday(&end, NULL);
    read_cpu_proc(&main_cpu_reading_after);

    // Calculate actual sleep duration in seconds (as double)
    double slept_time = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1.0e6;

    idle_reading = main_cpu_reading_after.idle_time - main_cpu_reading_before.idle_time;
    compute_time_reading = main_cpu_reading_after.compute_time - main_cpu_reading_before.compute_time;

    double output = 100.0 * (double)compute_time_reading / (compute_time_reading + idle_reading);
    if (output < 0.0) output = 0.0;
    if (output > 100.0) output = 100.0;

    if (show_diff_time == 1) {
        printf("%.6f %.2f\n", slept_time, output);  // Print sleep time and utilization
    } else {
        printf("%.2f\n", output);  // Print  utilization only
    }
    return 1;
}


int main(int argc, char **argv) {

    int c;
    int show_diff_time = 0;

    setvbuf(stdout, NULL, _IONBF, 0);
    user_hz = sysconf(_SC_CLK_TCK);

    while ((c = getopt (argc, argv, "i:hx")) != -1) {
        switch (c) {
        case 'h':
            printf("Usage: %s [-i msleep_time] [-h]\n\n",argv[0]);
            printf("\t-h      : displays this help\n");
            printf("\t-i      : specifies the milliseconds sleep time that will be slept between measurements\n\n");
            printf("\t-x      : show diff time before utilization\n\n");

            struct timespec res;
            double resolution;

            printf("\tEnvironment variables:\n");
            printf("\tUserHZ\t\t%ld\n", user_hz);
            clock_getres(CLOCK_REALTIME, &res);
            resolution = res.tv_sec + (((double)res.tv_nsec)/1.0e9);
            printf("\tSystemHZ\t%ld\n", (unsigned long)(1/resolution + 0.5));
            printf("\tCLOCKS_PER_SEC\t%ld\n", CLOCKS_PER_SEC);
            exit(0);
        case 'i':
            msleep_time = atoi(optarg);
            break;
        case 'x':
            show_diff_time = 1;
            break;
        default:
            fprintf(stderr,"Unknown option %c\n",c);
            exit(-1);
        }
    }

    while(1) {
        output_stats(show_diff_time);
    }

    return 0;
}