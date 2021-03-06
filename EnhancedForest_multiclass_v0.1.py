# encoding=utf-8

from sklearn.ensemble import RandomForestClassifier
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

import numpy as np
import random
import math
from scipy import stats

import ForestUtils
import time

class EnhancedForest():
    
    def __init__(self, train_len, test_len, isLRStacker):
        # self.pass_data_x_list = []
        self.pass_data_y_list = []
        self.pass_pred_y_list = []
        self.pass_pred_y_fold_list = []
        self.pass_pred_test_list = []
        self.pass_real_test_list = []

        self.train_len = train_len
        self.test_len = test_len
        self.isLRStacker = isLRStacker

    def predict_proba(self, X, num_class=None):
        y_preds = np.zeros((X.shape[0], len(self.estimator)))
        for i, clf in enumerate(self.estimator):
            if not num_class:
                y_pred = clf.predict_proba(X)[:,1]
            else:
                y_pred = clf.predict(X)
            y_preds[:, i] = y_pred

        if not num_class:
            return y_preds.mean(axis=1)
        else:
            m = stats.mode(y_preds, axis=1)
            return np.array([i[0] for i in m[0]])

    def predict_proba_lr(self, X, num_class=None):
        y_preds = np.zeros((X.shape[0], num_class))
        for i, clf in enumerate(self.estimator):
            y_pred = clf.predict_proba(X)
            y_preds[:, :] += y_pred/len(self.estimator)
        return self.log_model.predict(y_preds)

    def get_forest_leaf_index(self, clf, X_valid, y_valid, num_class):
        if num_class == None: num_class = 2

        forest_leaf_index = []
        for index, tree in enumerate(clf):
            # max dimension
            # max_dim = 0
            # get all data node id list
            node_id_lt_a = tree.apply(X_valid)
            node_id_cnt_a = np.bincount(node_id_lt_a)
            max_dim = np.max(node_id_lt_a) + 1
            # if tmp_dim_a > max_dim: max_dim = tmp_dim_a

            node_id_cnt_class = []
            for i in range(num_class):
                if len(X_valid[y_valid==i]) == 0: continue
                node_id_lt_tmp = tree.apply(X_valid[y_valid==i])
                node_id_cnt_tmp = np.bincount(node_id_lt_tmp)
                tmp_dim = np.max(node_id_lt_tmp) + 1
                if tmp_dim < max_dim:
                    diff = max_dim - tmp_dim
                    node_id_cnt_tmp = np.append(node_id_cnt_tmp, [0]*diff)
                # assert
                assert not any(~np.isfinite(node_id_cnt_tmp))
                node_id_cnt_class.append(node_id_cnt_tmp)
            node_id_cnt_class = np.array(node_id_cnt_class)
            
            # node_id_most
            node_id_cnt_m = np.max(node_id_cnt_class, axis=0)
            # node_id_cnt_p_n = np.vstack((node_id_cnt_p, node_id_cnt_n))
            node_id_argmax = np.argmax(node_id_cnt_class, axis=0)
            node_id_y_prob = np.array([1] * max_dim)
            for i in range(num_class):
                node_id_y_prob[node_id_argmax == i] = node_id_y_prob[node_id_argmax == i] * len(X_valid[y_valid==i])/len(X_valid)
            # node_id_argmin = np.argmin(node_id_cnt_p_n, axis=0)
            # node_id_argmax = node_id_argmax * len(X_valid[y_valid==0])/len(X_valid)
            # node_id_argmin = node_id_argmin * len(X_valid[y_valid==1])/len(X_valid)
            # node_id_y_prob = node_id_argmax + node_id_argmin

            # assert
            assert node_id_cnt_m.shape == node_id_cnt_a.shape
            # node_id_freq & node_id_count
            node_id_freq = node_id_cnt_m/node_id_cnt_a
            node_id_lift = node_id_freq/node_id_y_prob
            node_id_count = node_id_cnt_m/len(X_valid)
            # print(node_id_count, node_id_freq, node_id_count*node_id_freq)
            # node_id_score = node_id_count*node_id_freq
            # node_id_score = 2*node_id_freq*node_id_count/(node_id_freq+node_id_count)
            # node_id_score = 2*node_id_freq*node_id_lift/(node_id_freq+node_id_lift)
            node_id_score = node_id_freq


            # get positive data node id list
            # node_id_lt_p = tree.apply(X_valid[y_valid==1])
            # node_id_cnt_p = np.bincount(node_id_lt_p)
            # tmp_dim_p = np.max(node_id_lt_p)
            # if tmp_dim_p > max_dim: max_dim = tmp_dim_p
            # # get negative data node id list
            # node_id_lt_n = tree.apply(X_valid[y_valid==0])
            # node_id_cnt_n = np.bincount(node_id_lt_n)
            # tmp_dim_n = np.max(node_id_lt_n)
            # if tmp_dim_n > max_dim: max_dim = tmp_dim_n
            # # sync dimension
            # if tmp_dim_a < max_dim:
            #     diff = max_dim - tmp_dim_a
            #     node_id_cnt_a = np.append(node_id_cnt_a, [0]*diff)
            # if tmp_dim_p < max_dim:
            #     diff = max_dim - tmp_dim_p
            #     node_id_cnt_p = np.append(node_id_cnt_p, [0]*diff)
            # if tmp_dim_n < max_dim:
            #     diff = max_dim - tmp_dim_n
            #     node_id_cnt_n = np.append(node_id_cnt_n, [0]*diff)
            # # assert
            # assert not any(~np.isfinite(node_id_cnt_a))
            # assert not any(~np.isfinite(node_id_cnt_p))
            # assert not any(~np.isfinite(node_id_cnt_n))

            # node_id_most
            # node_id_cnt_m = np.maximum(node_id_cnt_p, node_id_cnt_n)
            # node_id_cnt_p_n = np.vstack((node_id_cnt_p, node_id_cnt_n))
            # node_id_argmax = np.argmax(node_id_cnt_p_n, axis=0)
            # node_id_argmin = np.argmin(node_id_cnt_p_n, axis=0)
            # node_id_argmax = node_id_argmax * len(X_valid[y_valid==0])/len(X_valid)
            # node_id_argmin = node_id_argmin * len(X_valid[y_valid==1])/len(X_valid)
            # node_id_y_prob = node_id_argmax + node_id_argmin

            # # assert
            # assert node_id_cnt_m.shape == node_id_cnt_a.shape
            # # node_id_freq & node_id_count
            # node_id_freq = node_id_cnt_m/node_id_cnt_a
            # node_id_lift = node_id_freq/node_id_y_prob
            # node_id_count = node_id_cnt_m/len(X_valid)
            # print(node_id_count, node_id_freq, node_id_count*node_id_freq)
            # node_id_score = node_id_count*node_id_freq
            # node_id_score = 2*node_id_freq*node_id_count/(node_id_freq+node_id_count)
            # node_id_score = 2*node_id_freq*node_id_lift/(node_id_freq+node_id_lift)
            node_id_score = node_id_freq

            # !!! FIXME: Maybe bugs
            node_id_score[np.isnan(node_id_score)] = 0
            node_id_score[np.isinf(node_id_score)] = 0
            assert not any(~np.isfinite(node_id_score))

            impurity_index = np.argsort(node_id_score, axis=0)[::-1]  
            impurity_sort = np.sort(node_id_score)[::-1]

            threshold_imp = np.mean(node_id_score[node_id_score>0], axis=0)
            # print(impurity_sort)
            now_tree_impurity_index = impurity_index[impurity_sort>threshold_imp]
            now_tree_impurity_sort = impurity_sort[impurity_sort>threshold_imp]
            # print(now_tree_impurity_index.shape, node_id_score.shape)
            # print(now_tree_impurity_index)
            # print(now_tree_impurity_sort)
            forest_leaf_index.append(now_tree_impurity_index)
        return forest_leaf_index


    def fit(self, X, y, verbose=True, feval=None, max_depth=None, random_state=1024, 
        min_samples_leaf=100, criterion='gini', num_class=None, kfold=3):
        
        kfold = kfold
        # sss = StratifiedShuffleSplit(n_splits=kfold, test_size=0.15, random_state=9487)
        sss = StratifiedKFold(n_splits=kfold, shuffle=True, random_state=9487)

        clf_folds = []
        p_all_fold = np.zeros(X.shape[0])
        if num_class:
            p_all_fold_prob = np.zeros((X.shape[0], num_class))
        est_leaf_index = []
        for i, (train_index, test_index) in enumerate(sss.split(X, y)):
            X_train, X_valid = X[train_index], X[test_index]
            y_train, y_valid = y[train_index], y[test_index]
        
            if verbose:
                print("X_train.shape, y_train.shape:"+str(X_train.shape)+str(y_train.shape))
                print("X_valid.shape, y_valid.shape:"+str(X_valid.shape)+str(y_valid.shape))
        
            clf = RandomForestClassifier(max_depth=max_depth, random_state=random_state, 
                                         min_samples_leaf=min_samples_leaf, n_estimators=200, n_jobs=-1,
                                         #max_leaf_nodes=100,
    #                                  n_estimators=2, n_jobs=8, oob_score=True, verbose=1, boostrap=False,
                                     criterion=criterion)
            clf = clf.fit(X_train, y_train)
            if verbose:
                print(clf)
                cross_score = cross_val_score(clf, X_valid, y_valid, cv=3)
                print("    cross_score: %.5f" % (cross_score.mean()))
            if not num_class:
                y_pred = clf.predict_proba(X_valid)[:,1]
            else:
                y_pred = clf.predict(X_valid)
                y_pred_prob = clf.predict_proba(X_valid)
                p_all_fold_prob[test_index] += y_pred_prob

            p_all_fold[test_index] += y_pred
            clf_folds.append(clf)

            ## vaild 
            forest_leaf_index = self.get_forest_leaf_index(clf, X_valid, y_valid, num_class)
            est_leaf_index.append(forest_leaf_index)

        self.est_leaf_index = est_leaf_index
        self.estimator = clf_folds
        # self.X_train = X_train
        # self.X_valid = X_valid
        # self.y_train = y_train
        # self.y_valid = y_valid
        if num_class:
            self.p_all_fold_prob = p_all_fold_prob
            log_model = LogisticRegression()
            log_model.fit(self.p_all_fold_prob, y)
            self.log_model = log_model
        
        # p_all
        if self.isLRStacker:
            p_all = self.predict_proba_lr(X, num_class)
        else:
            p_all = self.predict_proba(X, num_class)
        self.p_all = p_all
        self.p_all_fold = p_all_fold

        if not verbose:
            return self.estimator

        if feval == None:
            print("all data auc", roc_auc_score(y, p_all, labels=[0,1]))
        else:
            print("all data", feval(y, p_all, labels=[0,1]))

        # p_train
        if self.isLRStacker:
            p_train = self.predict_proba_lr(X_train, num_class)
        else:
            p_train = self.predict_proba(X_train, num_class)
        if feval == None:
            print("train data auc", roc_auc_score(y_train, p_train, labels=[0,1]))
        else:
            print("train data", feval(y_train, p_train, labels=[0,1]))

        # p_valid
        if self.isLRStacker:
            p_valid = self.predict_proba_lr(X_valid, num_class)
        else:
            p_valid = self.predict_proba(X_valid, num_class)
        if feval == None:
            print("valid data auc", roc_auc_score(y_valid, p_valid, labels=[0,1]))
        else:
            print("valid data", feval(y_valid, p_valid, labels=[0,1]))

        return self.estimator

    
    def get_threshold_of_impurity(self):
        impurity_list = np.array([])
        for est in self.estimator:
            for estimator in est:
                impurity = estimator.tree_.impurity
                impurity_list = np.hstack((impurity_list, impurity))
        mean_imp = np.mean(impurity_list, axis=0)
        self.threshold_imp = mean_imp

    def get_data_mask_of_tree(self, tree, X_train, verbose=True):
        estimator = tree
        impurity = estimator.tree_.impurity
        pass_node_id_lt = np.where(impurity <= self.threshold_imp)[0]

        node_id_lt = estimator.apply(X_train)
        pass_data_mask = np.isin(node_id_lt, pass_node_id_lt)

        return pass_data_mask

    def get_data_mask_of_forest(self, forest, X_train, verbose=True):
        last_tree_mask = np.array([True] * len(X_train))
        for index, tree in enumerate(forest):
            pass_tree_mask = self.get_data_mask_of_tree(tree, X_train, verbose)
            last_tree_mask = last_tree_mask & pass_tree_mask
            if verbose:
                print("%d [%d/%d] " % (index, len(pass_tree_mask[pass_tree_mask==True]), \
                    len(last_tree_mask[last_tree_mask==True])), end="")
        if verbose: print()
        return last_tree_mask

    def get_data_mask_of_ests(self, X_train, verbose=True):
        estimators = self.estimator
        last_forest_mask = np.array([True] * len(X_train))
        for index, forest in enumerate(estimators):
            pass_forest_mask = self.get_data_mask_of_forest(forest, X_train, verbose)
            last_forest_mask = last_forest_mask & pass_forest_mask
            if verbose:
                print("%d [%d/%d] " % (index, len(pass_forest_mask[pass_forest_mask==True]), \
                    len(last_forest_mask[last_forest_mask==True])), end="")
        if verbose: print()
        return last_forest_mask

    def get_data_mask_of_ests_vaild(self, X_train, verbose=True):
        estimators = self.estimator
        last_forest_mask = np.array([True] * len(X_train))
        for index, forest in enumerate(estimators):
            tree_leaf_index = self.est_leaf_index[index]
            for i_tree, tree in enumerate(forest):
                node_id_lt = tree.apply(X_train)
                pass_data_mask = np.isin(node_id_lt, tree_leaf_index[i_tree])
                last_forest_mask = last_forest_mask & pass_data_mask
                if verbose:
                    print("%d leaf-num:%d[now:%d/all:%d] " % (index, len(tree_leaf_index[i_tree]), \
                        len(pass_data_mask[pass_data_mask==True]), \
                        len(last_forest_mask[last_forest_mask==True])), end="")
            if verbose: print()
        return last_forest_mask

    def get_all_trees(self):
        trees = []
        for i, clf in enumerate(self.estimator):
            clf_trees = clf.estimators_
            trees.extend(clf_trees)
        return np.array(trees)

    def get_trees_sort_index(self, trees):
        impuritys = []
        for tree in trees:
            impurity = tree.tree_.impurity
            imp_mean = np.mean(impurity, axis=0)
            impuritys.append(imp_mean)

        trees_sort_index = np.argsort(impuritys, axis=0) 
        return trees_sort_index

    def get_dropout_trees(self, trees, last_len, trees_sort_index, dropout):
        max_len = math.ceil(dropout*last_len)
        dropout_index = trees_sort_index[:max_len]
        return trees[dropout_index]

    def dropout_train(self, X_train, dropout=0.8, verbose=True):
        # estimators = self.estimator.estimators_
        estimators = self.get_all_trees()
        trees_sort_index = self.get_trees_sort_index(estimators)
        max_loop = 50
        max_data_mask = np.array([False] * len(X_train))
        for loop in range(max_loop):
            if loop == 0: 
                sample_list = estimators
            elif len(last_tree_mask[last_tree_mask==True]) < 0.01*len(X_train):
                # sample_list = random.sample(estimators, math.ceil(dropout*len(sample_list)))
                sample_list = self.get_dropout_trees(estimators, len(sample_list), trees_sort_index, dropout)
            else:
                if len(last_tree_mask[last_tree_mask==True]) > len(max_data_mask[max_data_mask==True]):
                    max_data_mask = last_tree_mask
                break

            if loop > 0 and len(last_tree_mask[last_tree_mask==True]) > len(max_data_mask[max_data_mask==True]):
                max_data_mask = last_tree_mask
            last_tree_mask = np.array([True] * len(X_train))

            for index, tree in enumerate(sample_list):
                pass_tree_mask = self.get_data_mask_of_tree(tree, X_train, verbose)
                last_tree_mask = last_tree_mask & pass_tree_mask
                if verbose:
                    print("%d [%d/%d] " % (index, len(pass_tree_mask[pass_tree_mask==True]), \
                        len(last_tree_mask[last_tree_mask==True])), end="")
            if verbose: print()
            if verbose:
                print("loop: %d, len sample: %d, len pass: %d" % (loop, len(sample_list), len(last_tree_mask[last_tree_mask==True])))
        if verbose:
            print("loop: %d, len sample: %d, max pass: %d" % (loop, len(sample_list), len(max_data_mask[max_data_mask==True])))
        self.sample_trees = sample_list
        return max_data_mask

    def dropout_test(self, X_train, dropout=0.8, verbose=True):
        last_tree_mask = np.array([True] * len(X_train))
        for index, tree in enumerate(self.sample_trees):
            pass_tree_mask = self.get_data_mask_of_tree(tree, X_train, verbose)
            last_tree_mask = last_tree_mask & pass_tree_mask
            if verbose:
                print("%d [%d/%d] " % (index, len(pass_tree_mask[pass_tree_mask==True]), \
                    len(last_tree_mask[last_tree_mask==True])), end="")
        if verbose: print()
        return last_tree_mask

    def DataSplit(self, X_train, y_train, dropout=0.8, verbose=True):
        if dropout == None:
            pass_data_mask = self.get_data_mask_of_ests_vaild(X_train, verbose)
        elif dropout == -1:
            pass_data_mask = self.get_data_mask_of_ests(X_train, verbose)
        else:
            assert (dropout > 0 and dropout < 1)
            pass_data_mask = self.dropout_train(X_train, dropout, verbose)

        X_train_pass = X_train[pass_data_mask]
        y_train_pass = y_train[pass_data_mask]
        X_train_np = X_train[~pass_data_mask]
        y_train_np = y_train[~pass_data_mask]
        
        if verbose:
            print("pass data shape:" + str(X_train_pass.shape), y_train_pass[y_train_pass==1].shape)
            print("not pass data shape:" + str(X_train_np.shape), y_train_np[y_train_np==1].shape)
            print("all data shape:" + str(X_train_pass.shape[0]+X_train_np.shape[0]))

        positive = y_train_np[y_train_np==1]
        positive_pass = y_train_pass[y_train_pass==1]
        print("[p:%d/1:%d|n:%d/1:%d] " % (len(X_train_pass), len(positive_pass), len(X_train_np), len(positive)), end="")

        # self.X_train_pass = X_train_pass
        self.X_train_np = X_train_np
        # self.y_train_pass = y_train_pass
        self.y_train_np = y_train_np
        # self.p_all_pass = self.p_all[pass_data_mask]
        self.p_all_np = self.p_all[~pass_data_mask]
        # self.pass_data_x_list.append(X_train_pass)
        self.pass_data_y_list.append(y_train_pass)
        self.pass_pred_y_list.append(self.p_all[pass_data_mask])

        # self.p_all_fold_pass = self.p_all_fold[pass_data_mask]
        self.p_all_fold_np = self.p_all_fold[~pass_data_mask]
        self.pass_pred_y_fold_list.append(self.p_all_fold[pass_data_mask])
        # return X_train_pass, y_train_pass, X_train_np, y_train_np
    
    def TestDataSplit(self, X_test, real_y, dropout=0.8, num_class=None, verbose=True):
        """ Split Last Not Passed Test Data
            Return Passed Data Mask & Predict Probability
        Self
        ----
        pass_pred_test_list : list of passed predict_proba of test
        p_test_np : not passed predict_proba of test
        pass_real_test_list : list of passed real test label
        y_test_np : not passed real test label
    
        Parameters
        ----------
        X_test : last not passed X_test
        real_y : last not passed y_test
        
        Returns
        -------
        data_mask : passed data mask of last not passed X_test
        p_test : predict_proba of last not passed X_test
        """
        if dropout == None:
            data_mask = self.get_data_mask_of_ests_vaild(X_test, verbose)
        elif dropout == -1:
            data_mask = self.get_data_mask_of_ests(X_test, verbose)
        else:
            data_mask = self.dropout_test(X_test, dropout, verbose)
        
        if self.isLRStacker:
            p_test = self.predict_proba_lr(X_test, num_class)
        else:
            p_test = self.predict_proba(X_test, num_class)

        self.pass_pred_test_list.append(p_test[data_mask])
        self.p_test_np = p_test[~data_mask]
        self.pass_real_test_list.append(real_y[data_mask])
        self.y_test_np = real_y[~data_mask]
        return data_mask, p_test 
    
    def TrainModelLayer(self, X, y, X_test=None, all_data_mask=None, y_test=None, real_y=None, verbose=True, feval=None, 
            max_depth=10, random_state=1024, min_samples_leaf=10, criterion='gini', dropout=0.8, isFirst=False, num_class=None, kfold=3):
        """ TrainModelLayer
        Parameters
        ----------
        X : last not passed X_train
        y : last not passed y_train
        X_test : all test data X_test
        y_test : all predict test data y_test (change)
        real_y : all test data real_y
        all_data_mask : all test data pass mask
        
        Returns
        -------
        data_mask : passed data mask of last not passed X_test
        all_false_data_index : last not passed X_test
        """
        
        self.fit(X, y, verbose, feval, max_depth, random_state, min_samples_leaf, criterion, num_class, kfold)
        if isFirst: 
            if self.isLRStacker:
                p_test = self.predict_proba_lr(X_test, num_class)
            else:
                p_test = self.predict_proba(X_test, num_class)
            self.y_train_np = y
            self.y_test_np = real_y
            self.p_test_np = p_test
            self.p_all_np = self.p_all
            self.p_all_fold_np = self.p_all_fold
            self.X_train_np = X
            self.y_train_np = y
            y_test[:] = p_test[:]
            return self.estimator, np.array([False]*len(X_test)), all_data_mask, p_test
        self.get_threshold_of_impurity()
        self.DataSplit(X, y, dropout, verbose)

        if type(X_test) == type(None) or type(all_data_mask) == type(None) or type(y_test) == type(None):
            return self.estimator
        
        # X_test_np = X_test[~data_id_mask]
        all_false_data_index = np.where(all_data_mask == False)[0]
        X_test_np = X_test[all_false_data_index]
        y_test_np = real_y[all_false_data_index]
        data_mask, p_test = self.TestDataSplit(X_test_np, y_test_np, dropout, num_class, verbose)
        all_pass_data_index = all_false_data_index[data_mask]
        all_no_pass_data_index = all_false_data_index[~data_mask]
        y_test[all_pass_data_index] = p_test[data_mask]
        y_test[all_no_pass_data_index] = p_test[~data_mask]

        if verbose:
            pass_data_id = data_mask[data_mask==True]
            print("pass test data shape:", len(pass_data_id))
            print("not pass test data shape:", len(X_test_np) - len(pass_data_id))
        # if verbose and type(real_y) != type(None):
        #     if feval == None:
        #         print("pass train data auc", roc_auc_score(self.y_train_pass, self.p_all_pass))
        #         print("pass test data auc", roc_auc_score(real_y[all_pass_data_index], y_test[all_pass_data_index]))
        #     else:
        #         if len(self.p_all_pass) != 0:
        #             print("pass train data", feval(self.y_train_pass, self.p_all_pass))
        #         else:
        #             print("pass train data 0")
        #         if len(y_test[all_pass_data_index]) != 0:
        #             print("pass test data", feval(real_y[all_pass_data_index], y_test[all_pass_data_index]))
        #         else:
        #             print("pass test data 0")
        
        return self.estimator, data_mask, all_false_data_index, p_test
        
    def remove_last_items(self):
        del self.pass_pred_y_list[-1]
        del self.pass_data_y_list[-1]
        del self.pass_pred_y_fold_list[-1]
        del self.pass_real_test_list[-1]
        del self.pass_pred_test_list[-1]

    ##### ##### ##### ##### 
    ##### get some things
    ##### ##### ##### ##### 

    def getTrainLoss(self, feval=None):
        y_true = self.y_train_np.copy()
        for pass_data_y in self.pass_data_y_list:
            y_true = np.hstack((y_true, pass_data_y))
        y_pred = self.p_all_np.copy()
        for pass_pred_y in self.pass_pred_y_list:
            y_pred = np.hstack((y_pred, pass_pred_y))
        assert y_pred.shape[0] == self.train_len

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getPassTrainLoss(self, feval=None):
        y_true = np.array([])
        for pass_data_y in self.pass_data_y_list:
            y_true = np.hstack((y_true, pass_data_y))
        y_pred = np.array([])
        for pass_pred_y in self.pass_pred_y_list:
            y_pred = np.hstack((y_pred, pass_pred_y))

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getPassTrainLossNow(self, feval=None):
        if len(self.pass_data_y_list) == 0: return 0,0
        y_true = np.array(self.pass_data_y_list[-1])
        y_pred = np.array(self.pass_pred_y_list[-1])

        if len(y_pred) == 0: return 0,0
        # if len(y_true[y_true==1]) == 0 or len(y_true[y_true==0]) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getVaildLoss(self, feval=None):
        y_true = self.y_train_np.copy()
        for pass_data_y in self.pass_data_y_list:
            y_true = np.hstack((y_true, pass_data_y))
        y_pred = self.p_all_fold_np.copy()
        for pass_pred_y in self.pass_pred_y_fold_list:
            y_pred = np.hstack((y_pred, pass_pred_y))
        assert y_pred.shape[0] == self.train_len

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getPassVaildLoss(self, feval=None):
        y_true = np.array([])
        for pass_data_y in self.pass_data_y_list:
            y_true = np.hstack((y_true, pass_data_y))
        y_pred = np.array([])
        for pass_pred_y in self.pass_pred_y_fold_list:
            y_pred = np.hstack((y_pred, pass_pred_y))

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getPassVaildLossNow(self, feval=None):
        if len(self.pass_data_y_list) == 0: return 0,0
        y_true = np.array(self.pass_data_y_list[-1])
        y_pred = np.array(self.pass_pred_y_fold_list[-1])

        if len(y_pred) == 0: return 0,0
        # if len(y_true[y_true==1]) == 0 or len(y_true[y_true==0]) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getTestLoss(self, feval=None):
        y_true = self.y_test_np.copy()
        for pass_data_test in self.pass_real_test_list:
            y_true = np.hstack((y_true, pass_data_test))
        y_pred = self.p_test_np.copy()
        for pass_pred_test in self.pass_pred_test_list:
            y_pred = np.hstack((y_pred, pass_pred_test))
        assert y_pred.shape[0] == self.test_len

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)

    def getTestPred(self):
        y_pred = self.p_test_np.copy()
        for pass_pred_test in self.pass_pred_test_list:
            y_pred = np.hstack((y_pred, pass_pred_test))
        return y_pred

    def getPassTestLoss(self, feval=None):
        y_true = np.array([])
        for pass_data_test in self.pass_real_test_list:
            y_true = np.hstack((y_true, pass_data_test))
        y_pred = np.array([])
        for pass_pred_test in self.pass_pred_test_list:
            y_pred = np.hstack((y_pred, pass_pred_test))

        if len(y_pred) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)


    def getPassTestLossNow(self, feval=None):
        if len(self.pass_real_test_list) == 0: return 0,0
        y_true = np.array(self.pass_real_test_list[-1])
        y_pred = np.array(self.pass_pred_test_list[-1])

        if len(y_pred) == 0: return 0,0
        # if len(y_true[y_true==1]) == 0 or len(y_true[y_true==0]) == 0: return 0,0
        if feval == None:
            return roc_auc_score(y_true, y_pred, labels=[0,1])
        else:
            # return feval(y_true, y_pred, labels=[0,1])
            return feval(y_true, y_pred)