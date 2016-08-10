import re
import pandas as pd
import phosphosite_client as pc
import requests


def make_report(file):
    f = open(file).readlines()
    uid = file.strip().split('_')[0]
    peptide_list = [s.strip().split('\n')[0] for s in f]
    df = prune_list(peptide_list, uid)
    df_ptm = check_ptm_redundancy(df)
    df_ptm.to_csv('%s_report.csv' % uid, index=False)


def prune_list(peptide_list, uid):
    tryptic_petides = [p for p in peptide_list if _is_tryptic(p, uid)]
    l1, l2, l3, l4, l5, l6 = [], [], [], [], [], []
    for pep in tryptic_petides:
        score = score_(pep)
        l1.append(score[0])
        l2.append(score[1])
        l3.append(score[2])
        l4.append(score[3])
        l5.append(score[4])
        l6.append(score[5])

    df = pd.DataFrame(zip(tryptic_petides, l1, l2, l3, l4, l5, l6),
                      columns=['sequence', 'starts_with_EorDorQ',
                               'starts_with_KKorRRorRK',
                               'ends_with_KKorRRorRK',
                               'ends_with_KEorKDorRDorRE',
                               'length_crit', 'score'])
    return df


def _is_tryptic(peptide_seq, uid):
    tr = not verify_cm(peptide_seq) and verify_kr_end(
        peptide_seq, uid) and not verify_kr_inner(
            peptide_seq) and verify_preceeding(peptide_seq, uid)
    return tr


def verify_cm(peptide_seq):
    cm = bool(re.search('C', peptide_seq)) or bool(
        re.search('M', peptide_seq))
    return cm


def verify_kr_end(peptide_seq, uid):
    if verify_cterminal(peptide_seq, uid):
        end = True
        return end
    else:
        kr_end = bool(re.search('K$', peptide_seq)) or bool(
            re.search('R$', peptide_seq))
        return kr_end


def verify_kr_inner(peptide_seq):
    kr_inner = bool(re.search('K', peptide_seq[:-1])) or bool(
        re.search('R', peptide_seq[:-1]))
    return kr_inner


def verify_preceeding(peptide_seq, uid):
    url = 'http://www.uniprot.org/uniprot/%s.fasta' % uid
    r = requests.get(url)
    fasta_output = str(r.text)
    fasta_lines = fasta_output.strip().split('\n')
    protein_sequence = ''.join(fasta_lines[1:])
    start_ind = protein_sequence.find(peptide_seq)
    if start_ind >= 1:
        pa = protein_sequence[start_ind - 1]
    elif start_ind == 0:
        pa = 'n_terminal'
    elif start_ind == -1:
        pa = 'no match'
    if (pa == 'M') or (pa == 'K') or (pa == 'R') or (pa == 'n_terminal'):
        tryptic = True
    else:
        tryptic = False
    return tryptic


def verify_subsequent(peptide_seq, uid):
    url = 'http://www.uniprot.org/uniprot/%s.fasta' % uid
    r = requests.get(url)
    fasta_output = str(r.text)
    fasta_lines = fasta_output.strip().split('\n')
    protein_sequence = ''.join(fasta_lines[1:])
    start_ind = protein_sequence.find(peptide_seq)
    # index of subsequent amino acid
    next_ind = start_ind + len(peptide_seq)
    sa = protein_sequence[next_ind]
    return sa



def verify_cterminal(peptide_seq, uid):
    url = 'http://www.uniprot.org/uniprot/%s.fasta' % uid
    r = requests.get(url)
    fasta_output = str(r.text)
    fasta_lines = fasta_output.strip().split('\n')
    protein_sequence = ''.join(fasta_lines[1:])
    start_ind = protein_sequence.find(peptide_seq)
    if start_ind + len(peptide_seq) == len(protein_sequence):
        c_terminal = True
    else:
        c_terminal = False
    return c_terminal


def score_(peptide_seq):
    edq, kr, kre, ked, length_crit, score = False, False, False, False, False, 0
    if bool(re.search("^[E,D,Q]", peptide_seq)):
        edq = True
        score -= 1
    if bool(re.search("^KK", peptide_seq)) or bool(
            re.search("^RR", peptide_seq)) or bool(
                re.search("^RK", peptide_seq)):
        kr = True
        score -= 1
    if bool(re.search("KK$", peptide_seq)) or bool(
            re.search("RR$", peptide_seq)) or bool(
                re.search("RK$", peptide_seq)):
        kre = True
        score -= 1
    
    if bool(re.search("KE$", peptide_seq)) or bool(
            re.search("KD$", peptide_seq)) or bool(
                re.search("RD$", peptide_seq)) or bool(
                    re.search("RE$", peptide_seq)):
        ked = True
        score -= 1
    if not 5 <= len(peptide_seq) < 35:
        length_crit = True
        score -= 1
    return edq, kr, kre, ked, length_crit, score


def check_ptm_redundancy(df):

    query_list = ['\t'.join(['human', p])
                  for p in df.sequence.tolist()]
    query_list.insert(0, 'species\tsequence')

    query_string = '\n'.join(query_list)
    df_ptm = pc.get_ptms(query_string)

    # df_ptm = pd.read_table(filename, index_col=False)
    df_ptm['query_sequence'] = [seq.upper()
                                for seq in df_ptm.Sequence.tolist()]
    site_list = []
    redundancy_list_name = []
    redundancy_list_id = []

    for seq in df.sequence.tolist():
        red1 = df_ptm.Protein[df_ptm.query_sequence == seq].tolist()
        red2 = df_ptm.Accession[df_ptm.query_sequence == seq].tolist()
        redundancy_list_name.append([str(pr) for pr in red1
                                     if type(pr) == unicode])
        redundancy_list_id.append([str(pr).strip().split(':')[1] for pr in red2
                                   if type(pr) == unicode])
        sites = df_ptm.Site[df_ptm.query_sequence == seq].tolist()
        site_list.append([s for s in sites if type(s) == unicode])

    for i, l in enumerate(redundancy_list_id):
        if not l:
            redundancy_list_name[i] = 'unknown'
            redundancy_list_id[i] = 'unknown'
            # site_list[i] = 'unknown'

    for i, ptm in enumerate(site_list):
        if not ptm:
            site_list[i] = 'no PTM reported'

    df_update = df.copy()
    df_update['matches_name'] = redundancy_list_name
    df_update['matches_uid'] = redundancy_list_id
    df_update['PTM_sites'] = site_list

    return df_update

