#!/usr/bin/env python3

import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import glob

def maxDiff(row):
    max_diff = max(row) - min(row)
    return max_diff

def readResult(file, section="occupancy"):

    deletables = ['[*,*]', '(tr)', ':=', ';']
    endchar = ';'
    data = []

    with open(file) as datafile:
        reader = csv.reader(datafile, delimiter=' ', skipinitialspace=True)
        is_reading = False
        for row in reader:
            if is_reading:
                if row == [endchar]:
                    is_reading = False
                    break
                    # remove unnecessary AMPL symbols
                for i in deletables:
                    if i in row:
                        row.remove(i)
                data.append(row[1:])
            if section in row:
                # start reading next line
                is_reading = True

    df = pd.DataFrame(data)
    df = df.rename(columns=df.iloc[0])
    df = df.drop(df.index[0]).reset_index(drop=True)
    df = df.applymap(float)
    
    if section=="occupancy":
        df['delta'] = df.apply(maxDiff, axis=1)
        df['delta_mean'] = df['delta'].mean()
    return df

if __name__ == "__main__":
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 2,width_ratios=[7,1])
    gs.update(wspace=0.05)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharey=ax1)
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    ax2.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom='off',      # ticks along the bottom edge are off
            top='off',         # ticks along the top edge are off
            labelbottom='off') # labels along the bottom edge are off
    
    
    dfs = []
    for file in glob.glob("results/*.txt"):
        dfs.append(readResult(file))
    for i in range(len(dfs)):
        df = dfs[i]
        ax1.plot(df['delta'], ls=':', alpha=0.5, label='_nolegend_')
        if i == 0:
            ax2.plot(df['delta_mean'], ls=':', c='C0', alpha=0.5, label='Random sample')
        else:
            ax2.plot(df['delta_mean'], ls=':', c='C0', alpha=0.5, label='_nolegend_')
    mean = sum([x['delta_mean'][0] for x in dfs]) / len(dfs)
    ax2.plot(dfs[0].index.values, np.broadcast_to(mean, dfs[0].index.values.shape),
            ls='-', lw=5, c='C0', label='Random mean')
    
    
    bestdf = readResult("results/best.txt")
    ax1.plot(bestdf['delta'], c='C1', lw=3, label='_nolegend_')
    ax2.plot(bestdf['delta_mean'], c='C1', lw=5, label='Optimised')
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Daily ward difference')
    ax2.set_ylabel('Mean daily ward difference')
    ax2.legend(markerfirst=False)
    fig.suptitle('Comparison Between Optimized and Random Rosters')

    print("Best:", bestdf['delta_mean'][0], "\tMean:", mean, "\tDiff:",
          mean-bestdf['delta_mean'][0])
    
    fig.savefig('results/comparison.pdf', bbox_inches='tight')