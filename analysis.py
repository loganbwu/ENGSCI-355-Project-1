#!/usr/bin/env python3

import pandas as pd
pd.set_option('precision', 1)
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import glob
import statsmodels.stats.api as sms

save = True

def addRosterString(df):
    rosterList = []
    wardNums = {'LIME': 1,
                'NAVY': 2,
                'YELLOW': 3}
    for i in range(len(df)):
        for ward in df.columns.tolist()[:-1]:
            if df.iloc[(i+1)%len(df)][ward] > df.iloc[i][ward]:
                # population has increased today
                rosterList.append(wardNums[ward])
                break
    rosterString = ','.join([str(x) for x in rosterList])
    df.rosterString = rosterString  
    
def printRosterStrings(dfs):
    for df in dfs:
        addRosterString(df)
    for i, df in enumerate([df for df in dfs if not df.opt]):
        print("Roster", i+1)
        print(df.rosterString)

def maxDiff(row):
    max_diff = max(row) - min(row)
    return max_diff

def readResult(file, section="occupancy"):

    deletables = ['[*,*]', '(tr)', ':=', ';']
    endchar = ';'
    data = []
    
    obj = None
    opt = None

    with open(file) as datafile:
        reader = csv.reader(datafile, delimiter=' ', skipinitialspace=True)
        is_reading = False
        for row in reader:
            # pick out obj
            if 'objective:' in row:
                obj = float(row[-1])
            if 'optimise:' in row:
                opt = bool(int(row[-1]))
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
    df.index = df.index+1
    
    if section=="occupancy":
        df['delta'] = df.apply(maxDiff, axis=1)
        df.delta_mean = df['delta'].mean()
        df.obj = obj
        df.opt = opt
        df.arrangement = file.split('/')[-1].split('.')[0]
    return df


if __name__ == "__main__":
    fig = plt.figure(figsize=(8, 2.5))
    gs = gridspec.GridSpec(1, 2,width_ratios=[10,1])
    gs.update(wspace=0.05)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharey=ax1)
    ax1.set_xlim([1, 42])
    ax1.set_ylim([0, 64])
    ax1.xaxis.set_ticks(np.arange(7, 49, 7))
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    ax2.tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom='off',      # ticks along the bottom edge are off
            top='off',         # ticks along the top edge are off
            labelbottom='off') # labels along the bottom edge are off
    
    
    dfs = []
    for file in glob.glob("results/*/*.txt"):
        dfs.append(readResult(file))
        
    bestobj = np.inf
    bestdf = None
    
    for df in dfs:
        # pick out optimal solution
        if df.obj < bestobj and df.opt:
            bestdf = df
            bestobj = df.obj
            
        # plot random solutions
        if not df.opt:
            ax1.plot(df['delta'], ls='-', c='C0', alpha=0.25, label='_nolegend_')
            ax2.axhline(df.delta_mean, ls='-', c='C0', alpha=0.25, label='_nolegend_')
    
    # get random mean
    mean_unopt = np.mean([df.obj for df in dfs if not df.opt])/len(bestdf)
    ax1.axhline(mean_unopt, ls='-', lw=2, c='blue', label='_nolegend_')
    ax1.plot(bestdf['delta'], c='C1', lw=2, label='_nolegend_')
    
    # add dummy to legend
    ax2.plot(np.NaN, np.NaN, ls='-', c='C0', alpha=1, label='Unoptimised sample')
    
    ax2.axhline(mean_unopt, ls='-', lw=2, c='blue', label='Unoptimised mean')
    ax2.axhline(bestdf.delta_mean, c='C1', lw=2, label='Optimised')
    
    # plot formatting
    ax1.set_xlabel('Day')
    ax1.set_ylabel('Daily ward difference')
    ax2.set_xlabel('Mean')
    leg = ax2.legend(markerfirst=False)
    leg.get_frame().set_edgecolor('black')
    fig.suptitle('Comparison Between Optimised and Random Rosters')

    unopt_objs = [df.obj/len(bestdf) for df in dfs if not df.opt]
    unopt_objs_confint = sms.DescrStatsW(unopt_objs).tconfint_mean()
    opt_diffs = [bestdf.delta_mean-df.obj/len(bestdf) for df in dfs if not df.opt]
    opt_confint = sms.DescrStatsW(opt_diffs).tconfint_mean()
    print("Best: %.2f\tMean: %.2f\tDiff:%.2f (%.2f%%)" % (bestdf.delta_mean, 
          mean_unopt, mean_unopt-bestdf.delta_mean, 100*(bestdf.delta_mean-mean_unopt)/mean_unopt))
    print("Random sol confidence interval:", unopt_objs_confint)
    print("Improvement confidence interval:", opt_confint)
    
    if save:
        fig.savefig('results/comparison.pdf', bbox_inches='tight', pad_inches=0)
    
    # Analyse differences per arrangement:
    pairwise = pd.DataFrame(columns=('arrangement', 'unopt', 'opt', 'diff', 'pc_diff'))
    for df_unopt in [df for df in dfs if not df.opt]:
        # find matching optimised roster
        df_opt = [df for df in dfs if df.arrangement == df_unopt.arrangement and df.opt][0]
        mean_unopt = df_unopt.delta_mean
        mean_opt = df_opt.delta_mean
        diff = df_opt.obj - df_unopt.obj
        pc_diff = 100*diff / df_unopt.obj
        pairwise.loc[len(pairwise)] = [df.arrangement, df_unopt.obj, df_opt.obj, diff, pc_diff]
    
    print()
    print(pairwise.head())
    print('Pairwise difference confint:', sms.DescrStatsW(pairwise['diff']/42).tconfint_mean())
    