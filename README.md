# hyperv-ansible

Blueprint Ansible pour **gérer un environnement Hyper-V + SCVMM en multisite**.

Cette première version se concentre sur le **paramétrage de la Live Migration**:
- au niveau **noeud Hyper-V** ;
- au niveau **cluster/groupe** via **SCVMM**.

---

## Objectif

Permettre une configuration standardisée par défaut, puis des surcharges par site/cluster:
- tronc commun global (authentification, performance SMB/Compression, etc.) ;
- overrides par cluster (nombre de migrations simultanées, sous-réseaux autorisés, etc.).

---

## Arborescence

```text
.
├── inventories/
│   └── multisite/
│       ├── hosts.yml
│       └── group_vars/
│           └── all.yml
├── playbooks/
│   └── configure_livemigration.yml
└── roles/
    ├── hyperv_livemigration/
    │   └── tasks/
    │       └── main.yml
    └── scvmm_livemigration/
        └── tasks/
            └── main.yml
```

---

## Pré-requis

- Ansible avec collections Windows (au minimum `ansible.windows`).
- Connectivité WinRM vers les noeuds Hyper-V et le(s) serveur(s) SCVMM.
- Droits d'administration Hyper-V et droits SCVMM suffisants.
- Module PowerShell SCVMM (`VirtualMachineManager`) installé côté serveur de gestion SCVMM ciblé.

---

## Modèle d'inventaire multisite

Le fichier `inventories/multisite/group_vars/all.yml` définit:
- `live_migration`: paramètres globaux par défaut ;
- `sites`: liste des sites et clusters ;
- `scvmm`: informations de connexion au management server.

Exemple de logique:
- `live_migration` global = baseline.
- `sites.<site>.clusters[].live_migration` = surcharge locale.

---

## Exécution

### 1) Vérifier la syntaxe

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml --syntax-check
```

### 2) Appliquer la configuration

```bash
ansible-playbook -i inventories/multisite/hosts.yml playbooks/configure_livemigration.yml
```

---

## Ce que fait le playbook

### Hyper-V (`hyperv_nodes`)
Le rôle `hyperv_livemigration`:
- active/désactive la Live Migration ;
- configure le protocole d'authentification (`CredSSP` / Kerberos) ;
- configure l'option de performance (`SMB`, etc.) ;
- définit le nombre max de migrations simultanées ;
- limite les réseaux de migration si `use_any_network: false`.

### SCVMM (`scvmm_servers`)
Le rôle `scvmm_livemigration`:
- parcourt les clusters déclarés dans la structure multisite ;
- applique un paramètre de migration (exemple: maximum de migrations) via cmdlets SCVMM.

> ⚠️ Les cmdlets/paramètres SCVMM peuvent varier selon la version.
> Adaptez précisément `roles/scvmm_livemigration/tasks/main.yml` à votre version SCVMM.

---

## Étapes suivantes recommandées

- Ajouter un mode `check`/dry-run plus fin pour SCVMM.
- Ajouter la gestion des réseaux CSV / SMB Multichannel / QoS par site.
- Ajouter des variables chiffrées (`ansible-vault`) pour les credentials.
- Ajouter des tests CI (lint YAML + syntax-check playbook).
