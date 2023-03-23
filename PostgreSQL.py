import psycopg2
import json


class DBException(Exception):
    pass


def connect(dbname):
    import credentials
    try:
        con = psycopg2.connect(host=credentials.hostname, user=credentials.username, password=credentials.password,
                               dbname=credentials.database)
    except psycopg2.Error as e:
        raise DBException(e.message)

    return con


def create_tables(cur, con):
    try:
        cur.execute("DROP TABLE IF EXISTS uploads")
        cur.execute(
            "CREATE TABLE uploads("
            "id SERIAL PRIMARY KEY, "
            "user_id INT,"
            "filename TEXT, "
            "peak_list_file_names JSON, "
            "analysis_software JSON,"
            "provider JSON,"
            "audits JSON,"
            "samples JSON,"
            "analyses JSON,"
            "protocol JSON,"
            "bib JSON,"
            "spectra_formats JSON,"
            "upload_time DATE, "
            "default_pdb TEXT,"
            "contains_crosslinks BOOLEAN,"
            "upload_error TEXT,"
            "error_type TEXT,"
            "upload_warnings JSON,"
            "origin TEXT)"
        )

        # ToDo: not used atm
        # might be a good place to save ions here?
        # cur.execute("DROP TABLE IF EXISTS protocols")
        # cur.execute(
        #     "CREATE TABLE protocols("
        #     "id text PRIMARY KEY, "
        #     "upload_id INT,"
        #     "protocol JSON,"
        #     "ms2_tol FLOAT)"
        # )

        cur.execute("DROP TABLE IF EXISTS db_sequences")
        cur.execute(
            "CREATE TABLE db_sequences("
            "id text, "
            "upload_id INT,"
            "accession TEXT, "
            "protein_name TEXT, "
            "description TEXT, "
            "sequence TEXT, "
            "is_decoy BOOLEAN)"
        )
        cur.execute("DROP TABLE IF EXISTS peptides")
        cur.execute(
            "CREATE TABLE peptides("
            "id text, "
            "upload_id INT,"
            "seq_mods TEXT,"
            "link_site INT,"
            "crosslinker_modmass FLOAT,"    # ToDo: save cross-links to extra table?
            "crosslinker_pair_id INT)"
        )
        cur.execute("DROP TABLE IF EXISTS modifications")
        cur.execute(
            "CREATE TABLE modifications("
            "id BIGINT, "
            "upload_id INT,"
            "mod_name TEXT, "
            "mass FLOAT, "
            "residues TEXT, "
            "accession TEXT)"
        )
        cur.execute("DROP TABLE IF EXISTS peptide_evidences")
        cur.execute(
            "CREATE TABLE peptide_evidences("
            "upload_id INT,"
            "peptide_ref text, "
            "dbsequence_ref text, "
            "protein_accession text, "
            "pep_start int, "
            "is_decoy INT)"
        )
        cur.execute("DROP TABLE IF EXISTS spectra")
        cur.execute(
            "CREATE TABLE spectra("
            "id BIGINT, "
            "upload_id INT,"
            "peak_list text, "
            "peak_list_file_name text, "
            "scan_id TEXT, "
            "frag_tol TEXT,"
            "spectrum_ref TEXT)"
        )
        cur.execute("DROP TABLE IF EXISTS spectrum_identifications")
        cur.execute(
            "CREATE TABLE spectrum_identifications("
            "id BIGINT, "
            "upload_id INT,"
            "spectrum_id BIGINT, "
            "pep1_id TEXT, "
            "pep2_id TEXT, "
            "charge_state INT, "
            "pass_threshold BOOLEAN, "
            "rank INT,"
            "ions TEXT, "   # ToDo: find better place to store ions might be protocols
            "scores JSON,"  # IS JSON data type valid or does it have to be TEXT
            "exp_mz FLOAT,"
            "calc_mz FLOAT)"
        )
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)
    return True


def write_upload(inj_list, cur, con):
    try:
        cur.execute("""
    INSERT INTO uploads (
        user_id,
        filename,
        peak_list_file_names,
        spectra_formats,
        analysis_software,
        provider,
        audits,
        samples,
        analyses,
        protocol,
        bib,
        upload_time,
        origin,
        upload_warnings
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s) RETURNING id AS upload_id""", inj_list)
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)
    rows = cur.fetchall()
    return rows[0]


# def write_protocols(inj_list, cur, con):
#     return True

def write_db_sequences(inj_list, cur, con):
    try:
        cur.executemany("""
        INSERT INTO db_sequences (
            id,
            accession,
            protein_name,
            description,
            sequence,
            upload_id
        )
        VALUES (%s, %s, %s, %s, %s, %s) """, inj_list)
        #     con.commit()
        #
    except psycopg2.Error as e:
        raise DBException(e.message)

    return True


def write_peptides(inj_list, cur, con):
    try:
        cur.executemany("""
        INSERT INTO peptides (
            id,
            seq_mods,
            link_site,
            crosslinker_modmass,
            upload_id,
            crosslinker_pair_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)""", inj_list)
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)

    return True


def write_modifications(inj_list, cur, con):
    try:
        cur.executemany("""
          INSERT INTO modifications (
            id,
            upload_id,
            mod_name, 
            mass, 
            residues, 
            accession
          )
          VALUES (%s, %s, %s, %s, %s, %s)""", inj_list)
        con.commit()
    except psycopg2.Error as e:
        raise DBException(e.message)

    return True


def write_peptide_evidences(inj_list, cur, con):
    try:
        cur.executemany("""
        INSERT INTO peptide_evidences (        
            peptide_ref,
            dbsequence_ref,
            protein_accession,
            pep_start,
            is_decoy,
            upload_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)""", inj_list)
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)

    return True


def write_spectra(inj_list, cur, con):
    try:
        cur.executemany("""INSERT INTO spectra (id, peak_list, peak_list_file_name, scan_id, frag_tol, upload_id, spectrum_ref)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""", inj_list)
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)

    return True


def write_spectrum_identifications(inj_list, cur, con):
    try:
        cur.executemany("""
          INSERT INTO spectrum_identifications (
              id, 
              upload_id, 
              spectrum_id, 
              pep1_id, 
              pep2_id,
              charge_state, 
              rank, 
              pass_threshold, 
              ions, 
              scores,
              exp_mz,
              calc_mz
          ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s , %s, %s, %s, %s)""", inj_list)
        con.commit()

    except psycopg2.Error as e:
        raise DBException(e.message)

    return True
