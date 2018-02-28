
import numpy as np
from copy import deepcopy


def log_return(input_df, strat_params):
    # Get params from input dict
    momentum = strat_params.get('momentum', None)
    threshold = strat_params.get('threshold', None)

    output_df = deepcopy(input_df)

    # calculate the log returns
    output_df['returns'] = np.log(output_df['ask'] / output_df['ask'].shift(1))

    # derive the positioning according to the momentum chosen
    output_df['position'] = np.sign(output_df['returns'].rolling(momentum).mean())

    # Get latest entries based on threshold
    positions = output_df['position'].tail(threshold)

    # output positions based on threshold
    if all(positions == 1):
        return 'buy'
    elif all(positions == -1):
        return 'sell'
    else:
        return 'hold'
