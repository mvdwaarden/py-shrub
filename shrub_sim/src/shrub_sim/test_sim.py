import simpy
import random

# Global variables for simulation parameters
RANDOM_SEED = 42  # Seed for reproducible results
SIM_DURATION = 100  # Time units to run the simulation
SERVICE_TIME = 5  # Time a customer spends at the desk
ARRIVAL_INTERVAL = 7  # Average time between new customer arrivals


class ServiceDesk:
    """
    Represents the service desk (resource) that customers use.
    """

    def __init__(self, env):
        self.env = env
        # A simpy.Resource is the server (the single desk). Capacity is 1.
        self.desk = simpy.Resource(env, capacity=1)
        self.wait_times = []

    def serve(self, customer_name):
        """The process of being served at the desk."""

        # 1. The service takes a set amount of time (SERVICE_TIME)
        print(f'{self.env.now:.2f}: {customer_name} starts service.')
        yield self.env.timeout(SERVICE_TIME)

        print(f'{self.env.now:.2f}: {customer_name} finishes service.')


def customer(env, name, desk_model):
    """
    The customer process. A customer arrives, waits, gets served, and leaves.
    """
    arrival_time = env.now
    print(f'{arrival_time:.2f}: {name} arrives.')

    # 1. Request the resource (the desk)
    with desk_model.desk.request() as request:
        # Wait until the request is granted (until the desk is free)
        yield request

        # Calculate and record the waiting time
        wait = env.now - arrival_time
        desk_model.wait_times.append(wait)
        print(f'{env.now:.2f}: {name} is done waiting (waited {wait:.2f} units).')

        # 2. Use the resource (get served)
        yield env.process(desk_model.serve(name))

        # The 'with' block automatically releases the resource upon exiting.


def customer_generator(env, desk_model):
    """
    Generates new customer processes based on random arrivals.
    """
    customer_count = 0
    while True:
        # Generate the next customer
        customer_count += 1
        name = f'Customer {customer_count}'

        # Start the customer process
        env.process(customer(env, name, desk_model))

        # Wait a random time before generating the next customer
        t = random.expovariate(1.0 / ARRIVAL_INTERVAL)
        yield env.timeout(t)


# --- Simulation Setup and Run ---

# Setup
random.seed(RANDOM_SEED)
env = simpy.Environment()
desk_model = ServiceDesk(env)

# Start the customer generator process
env.process(customer_generator(env, desk_model))

# Run the simulation until SIM_DURATION is reached
print("--- Starting Service Desk Simulation ---")
env.run(until=SIM_DURATION)
print("--- Simulation Finished ---")

# --- Results Analysis ---
total_wait = sum(desk_model.wait_times)
num_served = len(desk_model.wait_times)

if num_served > 0:
    print(f'\nTotal Customers Served: {num_served}')
    print(f'Average Wait Time: {total_wait / num_served:.2f} units')
else:
    print('No customers were served.')