import requests
import re
import pandas as pd
import os

resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'resources')
df_map = pd.read_table(os.path.join(resource_path, 'hgnc_mapping.txt'))


def ensp2uid(ensp_id):
    """ Return Uniprot ID given Ensembl Protein ID 
    
    Parameter
    --------
    ensp_id: string
        Ensembl Protein ID
    
    Return
    ------
    id: string
       Uniprot_Id
    """
    url = "http://grch37.rest.ensembl.org/xrefs/id/"
    query = "%s?content-type=application/json;" % ensp_id
    db = "external_db=Uniprot/SWISSPROT"

    r = requests.get(url + query + db)
    dict = r.json()
    try:
        id = dict[0]['primary_id']
    except IndexError:
        id = 'unknown'
    except KeyError:
        id = 'unknown'
    return id


def name2entrez(name):
    """ Return Entrez Id given Gene Name
    
    Parameter
    --------
    name: string
        Gene Name/Symbol
    
    Return
    ------
    id: int
       Entrez ID
    """
    entrez_id = df_map[df_map['Approved Symbol'] == name][
        'Entrez Gene ID'].values[0]
    return int(entrez_id)


def entrez2name(entrez_id):
      """ Return Gene name given Entrez ID 
    
    Parameter
    ---------
    ensp_id: int
        Entrez ID
    
    Return
    ------
    id: string
       Gene Name/Symbol
    """
    gene_name = df_map[df_map['Entrez Gene ID'] == entrez_id][
        'Approved Symbol'].values[0]
    return gene_name



def uid2gn(uid):
    """ Return Gene name given Uniport Id
    
    Parameter
    ---------
    uid: string
       Uniprot ID

    Return
    ------
    gene_name: string
       Gene Name/ Symbol
    """
    uid = uid.split('-')[0]
    url = "http://www.uniprot.org/uniprot/%s.fasta" % uid

    r = requests.get(url)
    try:
        line1 = r.text.split('\n')[0]
        gene_name = re.search('GN=(.*) PE', line1).group(1)
    except AttributeError:
        gene_name = 'unknown'
    return gene_name


def get_uniprot_id(gene_name):
        """ Return Uniprot Id given Gene Name
    
    Parameter
    ---------
    gene_name: string
       Gene Name/Symbol

    Return
    ------
    uniprot_id: string
       Uniprot ID
    """   
    try:
        uniprot_id = df_map[df_map['Approved Symbol'] == gene_name][
            'UniProt ID(supplied by UniProt)'].values[0]
    except IndexError:
        uniprot_id = None
    except ValueError:
        uniprot_id = None
    return uniprot_id
