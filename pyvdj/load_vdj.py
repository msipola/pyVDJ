# Copyright 2019 Peter Vegh
#
# This file is part of pyVDJ.
#
# pyVDJ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyVDJ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyVDJ.  If not, see <https://www.gnu.org/licenses/>.


import pandas as pd
import pyvdj


def load_vdj(samples, adata = None):
    # Loads 10x V(D)J sequencing data into a dictionary containing a dataframe.
    # If anndata specified, returns it with an .uns['pyvdj'] slot, else
    # returns the dictionary.
    # samples: dict of path:samplename
    # paths point to filtered_contig_annotations.csv files
    samples_values = list(samples.values())
    if len(samples_values) != len(set(samples_values)):
        raise ValueError('Samplenames must be unique')
           # otherwise clonotypes are not assigned properly
    paths = list(samples.keys())
    cat_df = pd.DataFrame() # df for all V(D)J data
    for f in paths:
        df = pd.read_csv(f)
        df['barcode_meta'] = df['barcode'] + "_" + samples[f]
          # cell names, used for pairing cells in anndata to V(D)J data
          # values in this will have to match adata.obs['vdj_obs']

        df['clonotype_meta'] = df['raw_clonotype_id'] + "_" + samples[f]
          # making clonotype labels unique
        df['is_clone'] = ~df['raw_clonotype_id'].isin(['None'])
        df = df.loc[df['is_cell'] == True] # filter step
        df['sample'] = samples[f] # for subsetting in other functions

        cat_df = pd.concat([cat_df, df], ignore_index=True)

    # Flag as productive cell if all chains are productive:
    d = {'True': True, 'False': False, 'None': False}
    cat_df['productive'] = cat_df['productive'].map(d)
    is_productive = cat_df.groupby('barcode_meta')['productive'].apply(lambda g: all(g))
    product_dict = dict(zip(is_productive.index, is_productive))
    cat_df['productive_all'] = cat_df['barcode_meta']
    cat_df['productive_all'].replace(to_replace=product_dict, inplace=True)

    vdj_dict = {'df':cat_df, 'samples':samples, 'obs_col':'vdj_obs'}
      # for adata.uns

    if adata == None:
        return vdj_dict
    else:
        adata.uns['pyvdj'] = vdj_dict
        adata = pyvdj.add_obs(adata, obs = ['has_vdjdata'])
          # needed for making other annotations with add_obs()
        return adata
